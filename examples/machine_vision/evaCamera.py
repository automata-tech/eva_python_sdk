from evasdk import Eva


XYPosition = (float, float)
XYZPosition = (float, float, float)


POSE_GUESS = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
POSE_HOME = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
DEFAULT_END_EFFECTOR_ORIENTATION = {'w': 0.0, 'x': 0.0, 'y': 0.0, 'z': 0.0}


class EvaCamera:
    """
    EvaCamera is a wrapper around an Eva SDK object that can take an object
    position relative to the machine vision camera and move Eva's end
    effector to that object.
    """
    def __init__(self, eva: Eva, camera_relative_position: XYZPosition, camera_to_object_distance: float):
        self.__eva = eva
        self.__eva_offset_position_x = camera_relative_position[0]
        self.__eva_offset_position_y = camera_relative_position[1]
        self.__eva_offset_position_z = camera_relative_position[2] - camera_to_object_distance


    def move_to_camera_item(self, camera_item_postion: XYPosition):
        """
        Move Eva's end effector to the item position. Using the offset between
        where the camera is positioned, the distance between the camera and
        item and the items's x,y position, we calculate the position of the
        item relative to Eva. Using Inverse Kinamatics we then calculate a set
        of joint angles to get to the item position and move there.
        """
        camera_item_x, camera_item_y = camera_item_postion
        print(f'camera item x: {camera_item_x}, camera item y: {camera_item_y}')

        eva_relative_x = self.__eva_offset_position_x + camera_item_x
        eva_relative_y = self.__eva_offset_position_y + camera_item_y
        eva_relative_z = self.__eva_offset_position_z
        item_position = {'x': eva_relative_x, 'y': eva_relative_y, 'z': eva_relative_z}

        print(f'moving to item position {item_position}')
        with self.__eva.lock():
            to_item_joint_angles = self.__eva.calc_inverse_kinematics(POSE_GUESS, item_position, DEFAULT_END_EFFECTOR_ORIENTATION)
            self.__eva.control_go_to(to_item_joint_angles['ik']['joints'])

        print("in item position")


    def in_position_action(self):
        """
        Perform some action, for example in a pick and place use case you may
        activate a gripper. In this example we will just print out a message.
        """
        print("perform item action")


    def move_home(self):
        """
        Move back to a starting position. In practice for pick and place
        usecase you may want to place in a bin.
        """
        print("moving home")
        with self.__eva.lock():
            self.__eva.control_go_to(POSE_HOME)

        print("in home position")


def read_from_camera() -> XYPosition:
    """
    Your camera code here! in this simple example we assume the machine vision
    camera outputs an x and y position of the object detected in the frame at a
    known z offset.
    """
    return (1.6, 1.1)


if __name__ == "__main__":

    # initialize EvaCamera with a working Eva and the camera positional information
    eva = Eva("<IP_here>", "<token_here>")
    camera_position = (1.2, 2.3, 3.4)
    camera_to_item_distance = 2.2
    ec = EvaCamera(eva, camera_position, camera_to_item_distance)

    # read from the camera to get an item's position
    item_position = read_from_camera()

    # move eva to the item position and do some action
    ec.move_to_camera_item(item_position)
    ec.in_position_action()

    # move eva home
    ec.move_home()
