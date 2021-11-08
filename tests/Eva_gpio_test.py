import pytest

digital_inputs = [('d0', 'input'), ('d1', 'input'), ('d2', 'input'), ('d3', 'input'), ('ee_d0', 'input'), ('ee_d1', 'input')]
digital_outputs = [('d0', 'output'), ('d1', 'output'), ('d2', 'output'), ('d3', 'output'), ('ee_d0', 'output'), ('ee_d1', 'output')]
analog_inputs = [('ee_a0', 'input'), ('ee_a1', 'input')]
IOs = digital_inputs + analog_inputs + digital_outputs
# Not supported yet ('a0', 'input'), ('a1', 'input'), ('a0', 'output'), ('a1', 'output'), ('ee_a0', 'output'), ('ee_a1', 'output')


@pytest.mark.robot_required
class TestEva_GPIO:
    # TODO: currently fail on d1 inputs, requires fix
    def test_get(self, eva):
        # For all io variations, if the key is not present an exception
        # will be thrown so no assertions are required
        for pin in IOs:
            (pin_name, pin_type) = pin
            eva.gpio_get(pin_name, pin_type)


    def test_set(self, locked_eva):
        # All outputs should be set-able and idempotent
        for pin in digital_outputs:
            (pin_name, _) = pin
            locked_eva.gpio_set(pin_name, True)
            locked_eva.gpio_set(pin_name, True)
            locked_eva.gpio_set(pin_name, False)
            locked_eva.gpio_set(pin_name, False)


    def test_globals_edit(self, locked_eva):
        # For all io variations, if an error is encountered, an exception
        # will be thrown so no assertions are required
        locked_eva.globals_edit('outputs.ee_d0', True)
        locked_eva.globals_edit('outputs.d3', True)
        locked_eva.globals_edit(['outputs.ee_d0', 'outputs.d3'], [True, False])
        locked_eva.globals_edit(['outputs.ee_d0', 'outputs.d3'], [False, True])


    @pytest.mark.io_loopback_required
    def test_set_get(self, locked_eva):
        digital_states = [True, False]
        for state in digital_states:
            for (pin_name, _) in digital_outputs:
                locked_eva.gpio_set(pin_name, state)

            for (pin_name, pin_type) in digital_inputs:
                pin_state = locked_eva.gpio_get(pin_name, pin_type)
                assert(pin_state == state)
