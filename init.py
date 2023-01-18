from pyar3 import AR3_py3
from pyeyes import xy_beta

class correction:
    def __init__(self) -> None:
        ### Variable ###
        depth_pixels = [[0,240],[639,240],[320,0],[320,479]]  #[[0,0],[639,0],[0,479],[639,479]] # 640, 480
        c_depth_pixels = [320,240]

        ### Class ###
        arm = AR3_py3.AR3()
        eyes = xy_beta.realsense("D435")
        # arm.set_all_absolute(arm.standard_posture)
        # arm.zero_all()
        # for n in range(0,4):
        #     for depth_pixel in depth_pixels:
        #         dis = eyes.get_3d_camera_coordinate(depth_pixel)[0]
        #         print(round(dis,0))
        # arm.set_all_absolute(arm.standard_posture)
        # arm.set_one_absolute(0,90)
        arm.zero_all()

        arm.close()

if __name__=="__main__":
    correction()