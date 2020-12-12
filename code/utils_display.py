###############################################################################
### Useful function for visualization of face, hand and body pose estimation
###############################################################################

import cv2
import numpy as np
import open3d as o3d


class DisplayFace:
    def __init__(self, draw3d=False, max_num_faces=1, vis=None):
        super(DisplayFace, self).__init__()
        self.max_num_faces = max_num_faces
        self.nPt = 468 # Define number of keypoints/joints

        ############################
        ### Open3D visualization ###
        ############################
        if draw3d:
            if vis is not None:
                self.vis = vis
            else:
                self.vis = o3d.visualization.Visualizer()
                self.vis.create_window(width=640, height=480)
                self.vis.get_render_option().point_size = 3.0
            joint = np.zeros((self.nPt,3))

            # Draw face mesh
            # .obj file adapted from https://github.com/google/mediapipe/tree/master/mediapipe/modules/face_geometry/data
            self.mesh = o3d.io.read_triangle_mesh('../data/canonical_face_model.obj')
            self.mesh.paint_uniform_color([255/255, 172/255, 150/255]) # Skin color
            self.mesh.compute_vertex_normals()
            self.mesh.scale(0.01, np.array([0,0,0]))
            
            # Draw world reference frame
            frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5)

            # Add geometry to visualize
            self.vis.add_geometry(frame)
            self.vis.add_geometry(self.mesh)

            # Set camera view
            ctr = self.vis.get_view_control()
            ctr.set_up([0,-1,0]) # Set up as -y axis
            ctr.set_front([0,0,-1]) # Set to looking towards -z axis
            ctr.set_lookat([0.5,0.5,0]) # Set to center of view
            ctr.set_zoom(1)


    def draw2d(self, img, param):
        img_height, img_width, _ = img.shape

        # Loop through different faces
        for p in param:
            if p['detect']:
                # Draw contours around eyes, eyebrows, lips and entire face
                for connect in FACE_CONNECTIONS:
                    x = int(p['keypt'][connect[0],0])
                    y = int(p['keypt'][connect[0],1])
                    x_= int(p['keypt'][connect[1],0])
                    y_= int(p['keypt'][connect[1],1])
                    if x_>0 and y_>0 and x_<img_width and y_<img_height and \
                       x >0 and y >0 and x <img_width and y <img_height:
                        cv2.line(img, (x_, y_), (x, y), (0,255,0), 1) # Green

                # Loop through keypoint for each face
                for i in range(self.nPt):
                    x = int(p['keypt'][i,0])
                    y = int(p['keypt'][i,1])
                    if x>0 and y>0 and x<img_width and y<img_height:
                        # Draw keypoint
                        cv2.circle(img, (x, y), 1, (0,0,255), -1) # Red

            # Label fps
            if p['fps']>0:
                cv2.putText(img, 'FPS: %.1f' % (p['fps']),
                    (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)   

        return img


    def draw2d_(self, img, param):
        # Different from draw2d
        # draw2d_ draw 2.5D with relative depth info
        # The closer the landmark is towards the camera
        # The lighter the color of circle

        img_height, img_width, _ = img.shape

        # Loop through different hands
        for p in param:
            if p['detect']:
                # Draw contours around eyes, eyebrows, lips and entire face
                for connect in FACE_CONNECTIONS:
                    x = int(p['keypt'][connect[0],0])
                    y = int(p['keypt'][connect[0],1])
                    x_= int(p['keypt'][connect[1],0])
                    y_= int(p['keypt'][connect[1],1])
                    if x_>0 and y_>0 and x_<img_width and y_<img_height and \
                       x >0 and y >0 and x <img_width and y <img_height:
                        cv2.line(img, (x_, y_), (x, y), (255,255,255), 1) # White

                min_depth = min(p['joint'][:,2])
                max_depth = max(p['joint'][:,2])

                # Loop through keypt and joint for each face
                for i in range(self.nPt):
                    x = int(p['keypt'][i,0])
                    y = int(p['keypt'][i,1])
                    if x>0 and y>0 and x<img_width and y<img_height:
                        # Convert depth to color nearer white, further black
                        depth = (max_depth-p['joint'][i,2]) / (max_depth-min_depth)
                        color = [int(255*depth), int(255*depth), int(255*depth)]

                        # Draw keypoint
                        cv2.circle(img, (x, y), 2, color, -1)
            
            # Label fps
            if p['fps']>0:
                cv2.putText(img, 'FPS: %.1f' % (p['fps']),
                    (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)                           

        return img


    def draw3d(self, param):
        for i in range(self.max_num_faces):
            if param[i]['detect']:
                self.mesh.vertices = o3d.utility.Vector3dVector(param[i]['joint'])
            else:
                self.mesh.vertices = o3d.utility.Vector3dVector(np.zeros((self.nPt,3)))


class DisplayHand:
    def __init__(self, draw3d=False, max_num_hands=1, vis=None):
        super(DisplayHand, self).__init__()
        self.max_num_hands = max_num_hands

        # Define kinematic tree linking keypoint together to form skeleton
        self.ktree = [0,          # Wrist
                      0,1,2,3,    # Thumb
                      0,5,6,7,    # Index
                      0,9,10,11,  # Middle
                      0,13,14,15, # Ring
                      0,17,18,19] # Little

        # Define color for 21 keypoint
        self.color = [[0,0,0], # Wrist black
                      [255,0,0],[255,60,0],[255,120,0],[255,180,0], # Thumb
                      [0,255,0],[60,255,0],[120,255,0],[180,255,0], # Index
                      [0,255,0],[0,255,60],[0,255,120],[0,255,180], # Middle
                      [0,0,255],[0,60,255],[0,120,255],[0,180,255], # Ring
                      [0,0,255],[60,0,255],[120,0,255],[180,0,255]] # Little
        self.color = np.asarray(self.color)
        self.color_ = self.color / 255 # For Open3D RGB
        self.color[:,[0,2]] = self.color[:,[2,0]] # For OpenCV BGR
        self.color = self.color.tolist()


        ############################
        ### Open3D visualization ###
        ############################
        if draw3d:
            if vis is not None:
                self.vis = vis
            else:
                self.vis = o3d.visualization.Visualizer()
                self.vis.create_window(width=640, height=480)
                self.vis.get_render_option().point_size = 8.0
            joint = np.zeros((21,3))

            # Draw 21 joints
            self.pcd = []
            for i in range(max_num_hands):
                p = o3d.geometry.PointCloud()
                p.points = o3d.utility.Vector3dVector(joint)
                p.colors = o3d.utility.Vector3dVector(self.color_)
                self.pcd.append(p)
            
            # Draw 20 bones
            self.bone = []
            for i in range(max_num_hands):
                b = o3d.geometry.LineSet()
                b.points = o3d.utility.Vector3dVector(joint)
                b.colors = o3d.utility.Vector3dVector(self.color_[1:])
                b.lines  = o3d.utility.Vector2iVector(
                    [[0,1], [1,2],  [2,3],  [3,4],    # Thumb
                     [0,5], [5,6],  [6,7],  [7,8],    # Index
                     [0,9], [9,10], [10,11],[11,12],  # Middle
                     [0,13],[13,14],[14,15],[15,16],  # Ring
                     [0,17],[17,18],[18,19],[19,20]]) # Little
                self.bone.append(b)

            # Draw world reference frame
            frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5)

            # Add geometry to visualize
            self.vis.add_geometry(frame)
            for i in range(max_num_hands):
                self.vis.add_geometry(self.pcd[i])
                self.vis.add_geometry(self.bone[i])

            # Set camera view
            ctr = self.vis.get_view_control()
            ctr.set_up([0,-1,0]) # Set up as -y axis
            ctr.set_front([0,0,-1]) # Set to looking towards -z axis
            ctr.set_lookat([0.5,0.5,0]) # Set to center of view
            ctr.set_zoom(1)
            # ctr.set_up([0,-1,0]) # Set up as -y axis
            # ctr.set_front([1,0,0]) # Set to looking towards x axis
            # ctr.set_lookat([0,0,0.5]) # Set to center of view
            # ctr.set_zoom(0.5)


    def draw2d(self, img, param):
        img_height, img_width, _ = img.shape

        # Loop through different hands
        for p in param:
            if p['class'] is not None:
                # Label left or right hand
                x = int(p['keypt'][0,0]) - 30
                y = int(p['keypt'][0,1]) + 40
                # cv2.putText(img, '%s %.3f' % (p['class'], p['score']), (x, y), 
                cv2.putText(img, '%s' % (p['class']), (x, y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2) # Red
                
                # Loop through keypoint for each hand
                for i in range(21):
                    x = int(p['keypt'][i,0])
                    y = int(p['keypt'][i,1])
                    if x>0 and y>0 and x<img_width and y<img_height:
                        # Draw skeleton
                        start = p['keypt'][self.ktree[i],:]
                        x_ = int(start[0])
                        y_ = int(start[1])
                        if x_>0 and y_>0 and x_<img_width and y_<img_height:
                            cv2.line(img, (x_, y_), (x, y), self.color[i], 2) 

                        # Draw keypoint
                        cv2.circle(img, (x, y), 5, self.color[i], -1)
                        # cv2.circle(img, (x, y), 3, self.color[i], -1)

                        # # Number keypoint
                        # cv2.putText(img, '%d' % (i), (x, y), 
                        #     cv2.FONT_HERSHEY_SIMPLEX, 1, self.color[i])

                        # # Label visibility and presence
                        # cv2.putText(img, '%.1f, %.1f' % (p['visible'][i], p['presence'][i]),
                        #     (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, self.color[i])

                        # Label gesture
                        if p['gesture'] is not None:
                            size = cv2.getTextSize(p['gesture'].upper(), 
                                # cv2.FONT_HERSHEY_SIMPLEX, 2, 2)[0]
                                cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                            x = int((img_width-size[0]) / 2)
                            cv2.putText(img, p['gesture'].upper(),
                                # (x, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2)
                                (x, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

                            # Label joint angle
                            self.draw_joint_angle(img, p)

            # Label fps
            if p['fps']>0:
                cv2.putText(img, 'FPS: %.1f' % (p['fps']),
                    (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)   

        return img


    def draw2d_(self, img, param):
        # Different from draw2d
        # draw2d_ draw 2.5D with relative depth info
        # The closer the landmark is towards the camera
        # The lighter and larger the circle

        img_height, img_width, _ = img.shape

        # Loop through different hands
        for p in param:
            if p['class'] is not None:
                # Extract wrist pixel
                x = int(p['keypt'][0,0]) - 30
                y = int(p['keypt'][0,1]) + 40
                # Label left or right hand
                cv2.putText(img, '%s %.3f' % (p['class'], p['score']), (x, y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2) # Red

                min_depth = min(p['joint'][:,2])
                max_depth = max(p['joint'][:,2])

                # Loop through keypt and joint for each hand
                for i in range(21):
                    x = int(p['keypt'][i,0])
                    y = int(p['keypt'][i,1])
                    if x>0 and y>0 and x<img_width and y<img_height:
                        # Convert depth to color nearer white, further black
                        depth = (max_depth-p['joint'][i,2]) / (max_depth-min_depth)
                        color = [int(255*depth), int(255*depth), int(255*depth)]
                        size = int(10*depth)+2
                        # size = 2

                        # Draw skeleton
                        start = p['keypt'][self.ktree[i],:]
                        x_ = int(start[0])
                        y_ = int(start[1])
                        if x_>0 and y_>0 and x_<img_width and y_<img_height:
                            cv2.line(img, (x_, y_), (x, y), color, 2)

                        # Draw keypoint
                        cv2.circle(img, (x, y), size, color, size)
            
            # Label fps
            if p['fps']>0:
                cv2.putText(img, 'FPS: %.1f' % (p['fps']),
                    (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)                           

        return img


    def draw3d(self, param):
        for i in range(self.max_num_hands):
            if param[i]['class'] is None:
                self.pcd[i].points = o3d.utility.Vector3dVector(np.zeros((21,3)))
                self.bone[i].points = o3d.utility.Vector3dVector(np.zeros((21,3)))
            else:
                self.pcd[i].points = o3d.utility.Vector3dVector(param[i]['joint'])
                self.bone[i].points = o3d.utility.Vector3dVector(param[i]['joint'])


    def draw_joint_angle(self, img, p):
        # Create text
        text = None
        if p['gesture']=='Finger MCP Flexion':
            text = 'Index : %.1f \
                  \nMiddle: %.1f \
                  \nRing  : %.1f \
                  \nLittle : %.1f' % \
                (p['angle'][3], p['angle'][6], p['angle'][9], p['angle'][12])

        elif p['gesture']=='Finger PIP DIP Flexion':
            text = 'PIP: \
                  \nIndex : %.1f \
                  \nMiddle: %.1f \
                  \nRing  : %.1f \
                  \nLittle : %.1f \
                  \nDIP: \
                  \nIndex : %.1f \
                  \nMiddle: %.1f \
                  \nRing  : %.1f \
                  \nLittle : %.1f' % \
                (p['angle'][4], p['angle'][7], p['angle'][10], p['angle'][13],
                 p['angle'][5], p['angle'][8], p['angle'][11], p['angle'][14])

        elif p['gesture']=='Thumb MCP Flexion':
            text = 'Angle: %.1f' % p['angle'][1]

        elif p['gesture']=='Thumb IP Flexion':
            text = 'Angle: %.1f' % p['angle'][2]

        elif p['gesture']=='Thumb Radial Abduction':
            text = 'Angle: %.1f' % p['angle'][0]

        elif p['gesture']=='Thumb Palmar Abduction':
            text = 'Angle: %.1f' % p['angle'][0]

        elif p['gesture']=='Thumb Opposition':
            # Dist btw thumb and little fingertip
            dist = np.linalg.norm(p['joint'][4] - p['joint'][20])
            text = 'Dist: %.3f' % dist

        if text is not None:
            x0 = 10 # Starting x coor for placing text
            y0 = 60 # Starting y coor for placing text
            dy = 25 # Change in text vertical spacing        
            vert = len(text.split('\n'))
            # Draw black background
            cv2.rectangle(img, (x0, y0), (140, y0+vert*dy+10), (0,0,0), -1)
            # Draw text
            for i, line in enumerate(text.split('\n')):
                y = y0 + (i+1)*dy
                cv2.putText(img, line,
                    (x0, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)


    def draw_game_rps(self, img, param):
        img_height, img_width, _ = img.shape

        # Init result of 2 hands to none
        res = [None, None]

        # Loop through different hands
        for j, p in enumerate(param):
            # Only allow maximum of two hands
            if j>1:
                break

            if p['class'] is not None:                
                # Loop through keypoint for each hand
                for i in range(21):
                    x = int(p['keypt'][i,0])
                    y = int(p['keypt'][i,1])
                    if x>0 and y>0 and x<img_width and y<img_height:
                        # Draw skeleton
                        start = p['keypt'][self.ktree[i],:]
                        x_ = int(start[0])
                        y_ = int(start[1])
                        if x_>0 and y_>0 and x_<img_width and y_<img_height:
                            cv2.line(img, (x_, y_), (x, y), self.color[i], 2)

                        # Draw keypoint
                        cv2.circle(img, (x, y), 5, self.color[i], -1)

                # Label gesture 
                text = None
                if p['gesture']=='fist':
                    text = 'rock'
                elif p['gesture']=='five':
                    text = 'paper'
                elif (p['gesture']=='three') or (p['gesture']=='yeah'):
                    text = 'scissor'
                res[j] = text

                # Label result
                if text is not None:
                    x = int(p['keypt'][0,0]) - 30
                    y = int(p['keypt'][0,1]) + 40
                    cv2.putText(img, '%s' % (text.upper()), (x, y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2) # Red

        # Determine winner
        text = None
        winner = None
        if res[0]=='rock':
            if res[1]=='rock'     : text = 'Tie'
            elif res[1]=='paper'  : text = 'Paper wins'  ; winner = 1
            elif res[1]=='scissor': text = 'Rock wins'   ; winner = 0
        elif res[0]=='paper':
            if res[1]=='rock'     : text = 'Paper wins'  ; winner = 0
            elif res[1]=='paper'  : text = 'Tie'
            elif res[1]=='scissor': text = 'Scissor wins'; winner = 1
        elif res[0]=='scissor':
            if res[1]=='rock'     : text = 'Rock wins'   ; winner = 1
            elif res[1]=='paper'  : text = 'Scissor wins'; winner = 0
            elif res[1]=='scissor': text = 'Tie'

        # Label gesture
        if text is not None:
            size = cv2.getTextSize(text.upper(), 
                # cv2.FONT_HERSHEY_SIMPLEX, 2, 2)[0]
                cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            x = int((img_width-size[0]) / 2)
            cv2.putText(img, text.upper(),
                # (x, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2)
                (x, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)            

        # Draw winner text
        if winner is not None:
            x = int(param[winner]['keypt'][0,0]) - 30
            y = int(param[winner]['keypt'][0,1]) + 80
            cv2.putText(img, 'WINNER', (x, y), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2) # Yellow            

        return img


class DisplayBody:
    def __init__(self, draw3d=False, upper_body_only=True, vis=None):
        super(DisplayBody, self).__init__()

        # Define kinematic tree linking 33 keypoint together to form skeleton
        self.ktree = [
            0,     # Nose
            0,1,2, # Left eye
            0,4,5, # Right eye
            3,6,   # Ear
            10,9,  # Mouth
            23,11,11,12,13,14, # Upper body and arm
            15,16,17,18,15,16, # Hand
            24,12, # Torso
            23,24,25,26,27,28,27,28] # Leg

        # Define color for 33 keypoint
        self.color = [[60,0,255], # Nose
                      [60,0,255],[120,0,255],[180,0,255], # Left eye
                      [60,0,255],[120,0,255],[180,0,255], # Right eye
                      [240,0,255],[240,0,255], # Ear
                      [255,0,255],[255,0,255], # Mouth
                      [0,255,0],[60,255,0],[255,60,0],[0,255,60],[255,120,0],[0,255,120],
                      [255,180,0],[0,255,180],[255,240,0],[0,255,240],[255,255,0],[0,255,255],
                      [0,120,255],[0,180,255], # Torso
                      [255,60,0],[0,255,60],[255,120,0],[0,255,120],
                      [255,180,0],[0,255,180],[255,240,0],[0,255,240]]

        # Limit number of landmark, ktree and color to first 25 values
        self.num_landmark = 33
        if upper_body_only:
            self.num_landmark = 25
            self.ktree = self.ktree[:25]
            self.color = self.color[:25]

        self.color = np.asarray(self.color)
        self.color_ = self.color / 255 # For Open3D RGB
        self.color[:,[0,2]] = self.color[:,[2,0]] # For OpenCV BGR
        self.color = self.color.tolist()

        ############################
        ### Open3D visualization ###
        ############################
        if draw3d:
            if vis is not None:
                self.vis = vis
            else:
                self.vis = o3d.visualization.Visualizer()
                self.vis.create_window(width=640, height=480)
                self.vis.get_render_option().point_size = 8.0
            joint = np.zeros((self.num_landmark,3))

            # Draw joints
            self.pcd = o3d.geometry.PointCloud()
            self.pcd.points = o3d.utility.Vector3dVector(joint)
            self.pcd.colors = o3d.utility.Vector3dVector(self.color_)
            
            # Draw bones
            self.bone = o3d.geometry.LineSet()
            self.bone.points = o3d.utility.Vector3dVector(joint)
            self.bone.colors = o3d.utility.Vector3dVector(self.color_[1:])
            bone_connections = [[0,1],  [1,2], [2,3],    # Left eye
                                [0,4],  [4,5], [5,6],    # Right eye
                                [3,7],  [6,8],           # Ear
                                [9,10], [9,10],          # Mouth
                                [11,23],[11,12],[11,13],[12,14],[13,15],[14,16], # Upper body and arm
                                [15,17],[16,18],[17,19],[18,20],[15,21],[16,22], # Hand
                                [23,24],[12,24], # Torso
                                [23,25],[24,26],[25,27],[26,28],[27,29],[28,30],[27,31],[28,32]] # Leg

            if upper_body_only:
                bone_connections = bone_connections[:24]
            self.bone.lines  = o3d.utility.Vector2iVector(bone_connections)

            # Draw world reference frame
            frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5)

            # Add geometry to visualize
            self.vis.add_geometry(frame)
            self.vis.add_geometry(self.pcd)
            self.vis.add_geometry(self.bone)

            # Set camera view
            ctr = self.vis.get_view_control()
            ctr.set_up([0,-1,0]) # Set up as -y axis
            ctr.set_front([0,0,-1]) # Set to looking towards -z axis
            ctr.set_lookat([0.5,0.5,0]) # Set to center of view
            ctr.set_zoom(1)


    def draw2d(self, img, param):
        img_height, img_width, _ = img.shape

        p = param
        if p['detect']:
            # Loop through keypoint for body
            for i in range(self.num_landmark):
                x = int(p['keypt'][i,0])
                y = int(p['keypt'][i,1])
                if x>0 and y>0 and x<img_width and y<img_height:
                    # Draw skeleton
                    start = p['keypt'][self.ktree[i],:]
                    x_ = int(start[0])
                    y_ = int(start[1])
                    if x_>0 and y_>0 and x_<img_width and y_<img_height:
                        cv2.line(img, (x_, y_), (x, y), self.color[i], 2)

                    # Draw keypoint
                    cv2.circle(img, (x, y), 3, self.color[i], -1)

                    # Number keypoint
                    # cv2.putText(img, '%d' % (i), (x, y), 
                    #     cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.color[i])

                    # Label visibility and presence
                    # cv2.putText(img, '%.1f, %.1f' % (p['visible'][i], p['presence'][i]),
                    #     (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.color[i])

        # Label fps
        if p['fps']>0:
            cv2.putText(img, 'FPS: %.1f' % (p['fps']),
                (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)   

        return img


    def draw2d_(self, img, param):
        # Different from draw2d
        # draw2d_ draw 2.5D with relative depth info
        # The closer the landmark is towards the camera
        # The lighter and larger the circle

        img_height, img_width, _ = img.shape

        # Loop through different hands
        p = param
        if p['detect']:
            min_depth = min(p['joint'][:,2])
            max_depth = max(p['joint'][:,2])

            # Loop through keypt and joint for body hand
            for i in range(self.num_landmark):
                x = int(p['keypt'][i,0])
                y = int(p['keypt'][i,1])
                if x>0 and y>0 and x<img_width and y<img_height:
                    # Convert depth to color nearer white, further black
                    depth = (max_depth-p['joint'][i,2]) / (max_depth-min_depth)
                    color = [int(255*depth), int(255*depth), int(255*depth)]
                    size = int(5*depth)+2

                    # Draw skeleton
                    start = p['keypt'][self.ktree[i],:]
                    x_ = int(start[0])
                    y_ = int(start[1])
                    if x_>0 and y_>0 and x_<img_width and y_<img_height:
                        cv2.line(img, (x_, y_), (x, y), color, 2)

                    # Draw keypoint
                    cv2.circle(img, (x, y), size, color, size)
            
        # Label fps
        if p['fps']>0:
            cv2.putText(img, 'FPS: %.1f' % (p['fps']),
                (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)                           

        return img


    def draw3d(self, param):
        if param['detect']:
            self.pcd.points = o3d.utility.Vector3dVector(param['joint'])
            self.bone.points = o3d.utility.Vector3dVector(param['joint'])
        else:
            self.pcd.points = o3d.utility.Vector3dVector(np.zeros((self.num_landmark,3)))
            self.bone.points = o3d.utility.Vector3dVector(np.zeros((self.num_landmark,3)))


class DisplayHolistic:
    def __init__(self, draw3d=False, upper_body_only=True):

        ############################
        ### Open3D visualization ###
        ############################
        if draw3d:        
            self.vis = o3d.visualization.Visualizer()
            self.vis.create_window(width=640, height=480)
            self.vis.get_render_option().point_size = 8.0

            self.disp_face = DisplayFace(draw3d=draw3d, vis=self.vis)
            self.disp_hand = DisplayHand(draw3d=draw3d, vis=self.vis,
                max_num_hands=2)
            self.disp_body = DisplayBody(draw3d=draw3d, vis=self.vis,
                upper_body_only=upper_body_only)
        else:
            self.disp_face = DisplayFace(draw3d=draw3d)
            self.disp_hand = DisplayHand(draw3d=draw3d, max_num_hands=2)
            self.disp_body = DisplayBody(draw3d=draw3d, upper_body_only=upper_body_only)


    def draw2d(self, img, param):
        param_fc, param_lh, param_rh, param_bd = param
        self.disp_face.draw2d(img, [param_fc])
        self.disp_body.draw2d(img, param_bd)
        self.disp_hand.draw2d(img, [param_lh, param_rh])

        return img


    def draw2d_(self, img, param):
        param_fc, param_lh, param_rh, param_bd = param
        self.disp_face.draw2d_(img, [param_fc])
        self.disp_body.draw2d_(img, param_bd)
        self.disp_hand.draw2d_(img, [param_lh, param_rh])

        return img


    def draw3d(self, param):
        param_fc, param_lh, param_rh, param_bd = param
        self.disp_face.draw3d([param_fc])
        self.disp_hand.draw3d([param_lh, param_rh])
        self.disp_body.draw3d(param_bd)


# Adapted from https://github.com/google/mediapipe/blob/master/mediapipe/python/solutions/face_mesh.py
FACE_CONNECTIONS = frozenset([
    # Lips.
    (61, 146),
    (146, 91),
    (91, 181),
    (181, 84),
    (84, 17),
    (17, 314),
    (314, 405),
    (405, 321),
    (321, 375),
    (375, 291),
    (61, 185),
    (185, 40),
    (40, 39),
    (39, 37),
    (37, 0),
    (0, 267),
    (267, 269),
    (269, 270),
    (270, 409),
    (409, 291),
    (78, 95),
    (95, 88),
    (88, 178),
    (178, 87),
    (87, 14),
    (14, 317),
    (317, 402),
    (402, 318),
    (318, 324),
    (324, 308),
    (78, 191),
    (191, 80),
    (80, 81),
    (81, 82),
    (82, 13),
    (13, 312),
    (312, 311),
    (311, 310),
    (310, 415),
    (415, 308),
    # Left eye.
    (263, 249),
    (249, 390),
    (390, 373),
    (373, 374),
    (374, 380),
    (380, 381),
    (381, 382),
    (382, 362),
    (263, 466),
    (466, 388),
    (388, 387),
    (387, 386),
    (386, 385),
    (385, 384),
    (384, 398),
    (398, 362),
    # Left eyebrow.
    (276, 283),
    (283, 282),
    (282, 295),
    (295, 285),
    (300, 293),
    (293, 334),
    (334, 296),
    (296, 336),
    # Right eye.
    (33, 7),
    (7, 163),
    (163, 144),
    (144, 145),
    (145, 153),
    (153, 154),
    (154, 155),
    (155, 133),
    (33, 246),
    (246, 161),
    (161, 160),
    (160, 159),
    (159, 158),
    (158, 157),
    (157, 173),
    (173, 133),
    # Right eyebrow.
    (46, 53),
    (53, 52),
    (52, 65),
    (65, 55),
    (70, 63),
    (63, 105),
    (105, 66),
    (66, 107),
    # Face oval.
    (10, 338),
    (338, 297),
    (297, 332),
    (332, 284),
    (284, 251),
    (251, 389),
    (389, 356),
    (356, 454),
    (454, 323),
    (323, 361),
    (361, 288),
    (288, 397),
    (397, 365),
    (365, 379),
    (379, 378),
    (378, 400),
    (400, 377),
    (377, 152),
    (152, 148),
    (148, 176),
    (176, 149),
    (149, 150),
    (150, 136),
    (136, 172),
    (172, 58),
    (58, 132),
    (132, 93),
    (93, 234),
    (234, 127),
    (127, 162),
    (162, 21),
    (21, 54),
    (54, 103),
    (103, 67),
    (67, 109),
    (109, 10)
])  