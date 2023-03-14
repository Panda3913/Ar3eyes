from functools import lru_cache
import pyrealsense2 as rs
import numpy as np
from math import tan
import cv2

### test use ###
from imutils import contours
from imutils import perspective
from time import sleep
from math import sqrt,atan

class realsense:
    """
    Use
    ---
        >>> realsense = realsense("<camera_model>")
        >>> print(realsense.get_3d_camera_coordinate([0,0])[0])

    Parameter
    ---------
        `<camera_model>` value is 'D435' or 'D405'
    """
    
    def __init__(self,camera_model:str) -> None:

        ### setting camera fov ###
        if camera_model=="D435":
            self.fov_half = [0.39,0.36652]   # 69° × 42° -> 1.20428 0.73304 -> 0.60214 0.36652
        elif camera_model=="D405":
            self.fov_half = [0.75922,0.506145]  # 87° × 58° -> 1.51844 1.01229 -> 0.75922 0.506145
        else: raise ValueError(f"<camera_model> value is 'D435' or 'D405' (The current value is '{camera_model}') , in realsense.__init__" )

        ### realsense config ###
        self.pipeline = rs.pipeline()    									# 定義流程pipeline，創建一個管道
        config = rs.config()    											# 定義配置config
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 15) 	# 配置depth流
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)	# 配置color流
        self.pipeline.start(config)       					                # pipe_profile =  streaming流开始

        ### 創建對齊對象與color流對齊 ###
        align_to = rs.stream.color      									# align_to 是計劃對齊深度幀的流類型
        self.align = rs.align(align_to)     	 							# rs.align 執行深度幀與其他幀的對齊

    def get_aligned_images(self) -> list:
        """
        獲取對齊圖像幀與相機參數

        Returns
        ------
            [0] : color_intrin
            [1] : depth_intrin
            [2] : img_color [y,x]
            [3] : img_depth [y,x] ( end = [479,639] ) (mm)  # cm = mm/10
            [4] : aligned_depth_frame
        """

        frames = self.pipeline.wait_for_frames()     					# 等待獲取圖像幀，獲取顏色和深度的框架集
        aligned_frames = self.align.process(frames)      				# 獲取對齊幀，將深度框與顏色框對齊

        # aligned_depth = np.asanyarray(frames.get_depth_frame().get_distance(0,240))

        aligned_depth_frame = aligned_frames.get_depth_frame()			# 獲取對齊幀中的的depth幀
        aligned_color_frame = aligned_frames.get_color_frame() 			# 獲取對齊幀中的的color幀
        
        ### 獲取相機參數 ###
        depth_intrin = aligned_depth_frame.profile.as_video_stream_profile().intrinsics     # 獲取深度參數（像素坐標系轉相機坐標系會用到）
        color_intrin = aligned_color_frame.profile.as_video_stream_profile().intrinsics     # 獲取相機內參

        ### 將 images 轉為 numpy arrays ###
        img_color = np.asanyarray(aligned_color_frame.get_data())		# RGB圖 
        img_depth = np.asanyarray(aligned_depth_frame.get_data())   	# 深度圖（默認16位）

        return color_intrin, depth_intrin, img_color, img_depth, aligned_depth_frame

    def get_3d_camera_coordinate(self,depth_pixel:list=[320,240]) -> list:
        """
        獲取隨機點距離，三維坐標

        Returns
        ------
            [0] : distance
            [1] : camera coordinate
        """
        x = depth_pixel[0]
        y = depth_pixel[1]
        aligned_depth_frame = self.get_aligned_images()[4]
        depth_intrin = self.get_aligned_images()[1]
        dis = aligned_depth_frame.get_distance(x, y)        			# 獲取該像素點對應的深度,深度單位是m
        camera_coordinate = rs.rs2_deproject_pixel_to_point(depth_intrin, depth_pixel, dis)
        
        return dis*100, camera_coordinate
    

   
    def pixel(self,center_pixel:list = [320,240]) -> list:
        """
        像素長度 

        Return
        ------
            [x,y]  (mm)
        """
        dis,_ = self.get_3d_camera_coordinate(center_pixel)
        fov_half_x = self.fov_half[0]
        fov_half_y = self.fov_half[1]

        # HFOV = 2 atan[w/(2f)]
        # VFOV= 2 atan[h/(2f)]
        depth_intrin = self.get_aligned_images()[1]
        fx = depth_intrin.fx
        fy = depth_intrin.fy

        HFOV = atan(depth_intrin.width/(2*fx))
        VFOV = atan(depth_intrin.height/(2*fy))

        x = (dis*tan(HFOV))*2
        y = (dis*tan(VFOV))*2
        pixel_x = round(x/640,2)
        pixel_y = round(y/480,2)

        return pixel_x,pixel_y 

    def __distance_list(self) -> list:
        """
        距離陣列

        Return
        ------
            distance 2D array (mm)
        """
        dis_list = [[],[]]
        # coordinate_list = [[],[]] # (x,y,z)

        depth_pixel = self.get_aligned_images()[3]
        for j in range(0,476,17*2):
            for i in range(0,637,49):
                dis = depth_pixel[j, i]    # (320,240)(640,480)

                dis_list[len(dis_list)-1].append(int(dis))
                # coordinate_list[len(coordinate_list)-1].append(camera_coordinate)

            dis_list.append([])
            # coordinate_list.append([])

        dis_list = list(filter(None, dis_list))
        # coordinate_list = list(filter(None, coordinate_list))
        # correction_list = [coordinate_list[0][0][2],coordinate_list[0][-1][2],coordinate_list[-1][0][2],coordinate_list[-1][-1][2]]

        return dis_list #,correction_list

    def mask(self):
        """
        遮罩

        Return
        ------
            [0] : img_color
            [1] : img_gray
        """
        def midpoint(ptA,ptB):
            return ((ptA[0] + ptB[0]) * 0.5 , (ptA[1] + ptB[1]) * 0.5)
        def distance(ptA,ptB):
            return round(abs(sqrt((ptA[0]-ptB[0])**2+(ptA[1]-ptB[1])**2)),2)

        mask_list = np.zeros((480,640,3), dtype='uint8')
        # dis_list ,correction_list = self.get_3d_camera_coordinate()
        # co = cv2.cvtColor(__mask_list,cv2.COLOR_BGR2GRAY)

        ### get frame ###
        depth_pixels = self.get_aligned_images()[3]
        img_color = self.get_aligned_images()[2]
        
        
        # mean = (depth_pixels[240,1]+depth_pixels[240,639]+depth_pixels[0,320]+depth_pixels[479,320])/4 # np.average(depth_pixels)
        mean = np.average(depth_pixels)
        for j in range(1,476):
            for i in range(1,639):
        
                if depth_pixels[j,i] < mean:
                    mask_list[j,i] = [255,255,255]
         
        ### draw contours ###
        img_gray = cv2.cvtColor(mask_list,cv2.COLOR_BGR2GRAY)
        contours,_=cv2.findContours(img_gray,cv2.RETR_TREE ,cv2.CHAIN_APPROX_NONE)
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if area > 5000: 
                box = cv2.minAreaRect(contour)
                box = cv2.boxPoints(box)
                box = box.astype('int')
                box = perspective.order_points(box)
                cv2.drawContours(img_color,[box.astype(int)],0,(255,0,0),2)
                
                M = cv2.moments(contour)
                object_x = int(M['m10']/M['m00'])
                object_y = int(M['m01']/M['m00'])
                # for x,y in box:
                #     cv2.circle(frame,(int(x),int(y)),5,(0,0,255),3)

                (tl,tr,br,bl) = box 
                (tltrX,tltrY) = midpoint(tl,tr)
                (tlblX,tlblY) = midpoint(tl,bl)
                (blbrX,blbrY) = midpoint(bl,br)
                (trbrX,trbrY) = midpoint(tr,br)


                ## 4個角 之 點
                # cv2.circle(img_color,(int(tltrX),int(tltrY)),5,(183,197,57),-1)
                # cv2.circle(img_color,(int(tlblX),int(tlblY)),5,(183,197,57),-1)
                # cv2.circle(img_color,(int(blbrX),int(blbrY)),5,(183,197,57),-1)
                # cv2.circle(img_color,(int(trbrX),int(trbrY)),5,(183,197,57),-1)

                ## 中心點 之 連線
                # cv2.line(img_color,(int(tltrX),int(tltrY)),(int(blbrX),int(blbrY)),(255,0,0),2)
                # cv2.line(img_color,(int(tlblX),int(tlblY)),(int(trbrX),int(trbrY)),(255,0,0),2)

                pixel_x,pixel_y = self.pixel()
                dis_x = round(distance(tr,tl)*pixel_x,3)
                dis_y = round(distance(bl,tl)*pixel_y,3)
                dif_x = 320-object_x
                dif_y = 240-object_y

                ## 邊常 之 長度
                # cv2.putText(img_color,str(dis_x),(int(tltrX)-10,int(tltrY)),cv2.FONT_HERSHEY_COMPLEX,0.6,(255,255,255),1)
                # cv2.putText(img_color,str(dis_y),(int(trbrX)-10,int(trbrY)),cv2.FONT_HERSHEY_COMPLEX,0.6,(255,255,255),1)

                ## 物體 之 中心點
                cv2.circle(img_color,(int(object_x),int(object_y)),5,(183,197,57),-1)

                cv2.circle(img_color,(320,240),5,(183,197,57),-1)
                cv2.line(img_color,(320,240),(int(object_x),int(object_y)),(255,0,0),2)
                
                # print(dis)
                try:
                    cv2.putText(img_color,str(f"[{dif_x*pixel_x},{dif_y*pixel_y}]"),(int(object_x),int(object_y)),cv2.FONT_HERSHEY_COMPLEX,0.6,(255,255,255),1)
                except:
                    pass
        return img_color, img_gray
    
    def object_info(self):
        """
        取得所有物體 之 資訊
        
        Return
        ------
            [n]['center']       : [object_x,object_y]
            [n]['center_depth'] : 中點深度
            [n]['endpoint']     : 4個端點
            [n]['difference_px']: 離 中心點 之 距離 (像素)
            [n]['difference_m'] : 離 中心點 之 距離 (公分)
        """
        frame_center = [320,240]
        rt = []
        mask_list = np.zeros((480,640,3), dtype='uint8')
        depth_pixels = self.get_aligned_images()[3]

        mean = np.average(depth_pixels)
        for j in range(1,476):
            for i in range(1,639):
                if depth_pixels[j,i] < mean:
                    mask_list[j,i] = [255,255,255]

        ### contours ###
        img_gray = cv2.cvtColor(mask_list,cv2.COLOR_BGR2GRAY)
        contours,_=cv2.findContours(img_gray,cv2.RETR_TREE ,cv2.CHAIN_APPROX_NONE)
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if area > 5000: 
                box = cv2.minAreaRect(contour)
                box = cv2.boxPoints(box)
                box = box.astype('int')
                box = perspective.order_points(box)
                (tl,tr,br,bl) = box 
                M = cv2.moments(contour)
                object_x = int(M['m10']/M['m00'])
                object_y = int(M['m01']/M['m00'])

                dis_x = frame_center[0]-object_x
                dis_y = frame_center[1]-object_y
                # print(f"{frame_center[0]},{object_x}")
                # print(f"{frame_center[1]},{object_y}")
                pixel = self.pixel()
                try:
                    rt.append({'center':[object_x,object_y],
                        'center_depth':depth_pixels[object_x,object_y],
                        'endpoint':[tl.tolist(),tr.tolist(),br.tolist(),bl.tolist()],
                        'difference_px':[dis_x,dis_y],
                        'difference_cm':[dis_x*pixel[0],dis_y*pixel[1]]  
                        })
                except Exception as e:
                    raise ValueError("in object_info()")

        return rt

if __name__=="__main__":    
    realsense = realsense("D435")
    sleep(1)
    # HFOV = 2 atan[w/(2f)]
    # VFOV= 2 atan[h/(2f)]
    depth_intrin = realsense.get_aligned_images()[1]
 
    print(realsense.pixel())

    print(depth_intrin.ppx)
    
    
    # print(realsense.object_info()[0]['endpoint']) # 640,480
    while True:
        
        img_color,img_gray = realsense.mask()
        

        cv2.imshow("cap",img_color)
        cv2.imshow("cp",img_gray)

        key = cv2.waitKey(1)
        if  key == ord('q') or key == 27:
            break
    

    