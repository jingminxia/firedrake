from pyadjoint.tape import annotate_tape, stop_annotating, get_working_tape
from pyadjoint.overloaded_type import create_overloaded_object
from firedrake.adjoint.blocks import AssembleBlock, PointwiseOperatorBlock
import ufl


def annotate_assemble(assemble):
    def wrapper(*args, **kwargs):
        """When a form is assembled, the information about its nonlinear dependencies is lost,
        and it is no longer easy to manipulate. Therefore, we decorate :func:`.assemble`
        to *attach the form to the assembled object*. This lets the automatic annotation work,
        even when the user calls the lower-level :py:data:`solve(A, x, b)`.
        """
        annotate = annotate_tape(kwargs)
        with stop_annotating():
            output = assemble(*args, **kwargs)

        form = args[0]
        if isinstance(output, float):
            if not annotate:
                return output

            tape = get_working_tape()

            coeff_form = form.coefficients()
            extops_form = []
            for coeff in coeff_form:
                if isinstance(coeff, ufl.ExternalOperator):
                    extops_form += [coeff]
                    block_extops = PointwiseOperatorBlock(coeff, *args, **kwargs)
                    tape.add_block(block_extops)

                    block_variable = coeff.block_variable
                    block_extops.add_output(block_variable)

            output = create_overloaded_object(output)
            block = AssembleBlock(form)
            tape.add_block(block)

            block.add_output(output.block_variable)
        else:
            # Assembled a vector or matrix
            output.form = form

        return output

    return wrapper