from firedrake import *
from firedrake.supermeshing import *
import pytest


@pytest.fixture(params=[2, 3])
def mesh(request):
    if request.param == 2:
        return UnitSquareMesh(2, 3)
    if request.param == 3:
        return UnitCubeMesh(3, 2, 1)


@pytest.fixture(params=["scalar", "vector", "tensor"])
def shapify(request):
    if request.param == "scalar":
        return lambda x: x
    elif request.param == "vector":
        return VectorElement
    elif request.param == "tensor":
        return TensorElement
    else:
        raise RuntimeError


@pytest.fixture(params=["CG", "DG"])
def family_A(request):
    return request.param


@pytest.fixture(params=["CG", "DG"])
def family_B(request):
    return request.param


@pytest.fixture(params=[0, 1, 2, 3])
def degree_A(request):
    return request.param


@pytest.fixture(params=[0, 1, 2, 3])
def degree_B(request):
    return request.param


def test_galerkin_projection(mesh, shapify, family_A, family_B, degree_A, degree_B):
    if degree_A == 0 and family_A != "DG":
        return
    if degree_B == 0 and family_B != "DG":
        return
    if degree_B < degree_A:
        return
    if family_A == "DG" and family_B == "CG":
        return

    base = mesh
    mh = MeshHierarchy(base, 1)

    mesh_A = mh[-2]
    mesh_B = mh[-1]

    ele_A = shapify(FiniteElement(family_A, mesh_A.ufl_cell(), degree_A))
    V_A = FunctionSpace(mesh_A, ele_A)
    ele_B = shapify(FiniteElement(family_B, mesh_B.ufl_cell(), degree_B))
    V_B = FunctionSpace(mesh_B, ele_B)

    f_A = Function(V_A)

    with f_A.dat.vec_wo as x:
        x.setRandom()

    f_B_prolong = Function(V_B)
    prolong(f_A, f_B_prolong)

    solver_parameters = {
        "mat_type": "aij",
        "ksp_type": "preonly",
        "pc_type": "lu",
        "pc_factor_mat_solver_type": "mumps",
    }

    f_B_project = project(f_A, V_B, solver_parameters=solver_parameters)

    diff = Function(V_B)
    diff.assign(f_B_prolong - f_B_project)
    norm = sqrt(assemble(inner(diff, diff)*dx))

    print("|f_B_prolong - f_B_project|: %s" % norm)
    assert norm < 1.0e-12


if __name__ == "__main__":

    class ThereMustBeABetterWay(object):
        param = 2

    test_galerkin_projection(mesh(ThereMustBeABetterWay()), lambda x: x, "CG", "CG", 2, 3)
