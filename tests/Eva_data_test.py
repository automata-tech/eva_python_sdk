from evasdk import EvaError
import pytest


@pytest.mark.robot_required
class TestEva_Data:
    # TODO: we may want to check the structure of the snapshot JSON object
    def test_snapshot(self, eva):
        snapshot = eva.data_snapshot()
        assert(snapshot)
        assert(snapshot['control']['loop_count'] >= 0)


    def test_snapshot_property(self, eva):
        control_snapshot = eva.data_snapshot_property('control')
        assert(control_snapshot)
        assert(control_snapshot['loop_count'] >= 0)


    def test_data_snapshot_property_PropertNotPresent(self, eva):
        with pytest.raises(EvaError):
            eva.data_snapshot_property('rubbish_property')


    def test_servo_positions(self, eva):
        servo_positions = eva.data_servo_positions()
        assert(len(servo_positions) == 6)
