# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

#  True Motion Blur add-on
#  TMB Render
#  (c) 2020 Andrey Sokolov (so_records)

import bpy, time, datetime, pathlib, shutil
import numpy as np
from .tmb_support import TMB_Helpers
from bpy.props import BoolProperty, StringProperty, IntProperty
from bpy.utils import register_class, unregister_class
from time import perf_counter

#------------------ Add and remove Viewer for correct preview ------------------

class TMB_UpdatePreview(bpy.types.Operator):
    '''Add and remove Viewer to update render preview display'''
    bl_idname = "tmb.update"
    bl_label = "Update Preview"
    
    store = None
    project = None
    sc = None
    resx = None
    resy = None
    resprc = None
    pixlen = None
    timer = None
    viewer = None
    viewer_image = None
    wm = None
    win = None
        
    def structure(self):
        self.store = bpy.types.TMB_OT_store.store
        self.project = self.store['Project']
        self.sc = self.project['main_sc']
        self.wm = self.project['wm']
        self.win = self.project['window']
        self.resprc = self.sc.render.resolution_percentage/100
        self.resx = int(self.sc.render.resolution_x*self.resprc)
        self.resy = int(self.sc.render.resolution_y*self.resprc)
        self.pixlen = self.project['pix_len']
        self.viewer = None
        self.viewer_image = (
            bpy.data.images['Viewer Node']
            if 'Viewer Node' in bpy.data.images else
            bpy.data.images.new('Viewer Node', self.resx, self.resy)
            )
        self.viewer_image.pixels[:] = np.ones(
            len(self.viewer_image.pixels))[:]
        self.timer = None
    
    def timer_add(self, tick=0.01):
        '''Add timer event and set it as self.timer'''
        self.timer = self.wm.event_timer_add(tick, window=self.win)
    
    def timer_remove(self):
        '''Remove timer event and clear self.timer'''
        try:
            for _ in range(3):
                self.wm.event_timer_remove(self.timer)
        except:
            pass
        self.timer = None

    def viewer_add(self):
        self.viewer = self.sc.node_tree.nodes.new('CompositorNodeViewer')
        self.viewer.name = 'TMB_Viewer'
        self.viewer.location.x += 500
        self.viewer.location.y -= 100
    
    def viewer_remove(self):
        self.sc.node_tree.nodes.remove(self.viewer)
        self.viewer = None
        
    def cleanup(self):
        self.viewer_image = None
        self.viewer = None
        self.wm = None
        self.sc = None
        self.resx = None
        self.resy = None
        self.resprc = None
        self.pixlen = None
        self.project = None
        self.store = None
        self.win = None
    
    def execute(self, context):
        self.structure()
        self.viewer_add()
        self.timer_add()
        self.wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        if event.type == 'ESC':
            self.cleanup()
            return {'CANCELLED'}
        elif event.type == 'TIMER':
            if (
                self.viewer_image.pixels ==
                np.ones(len(self.viewer_image.pixels)).all()
            ):
                return {'PASS_THROUGH'}
            else:
                self.timer_remove()
                self.viewer_remove()
                self.cleanup()
                return {'FINISHED'}
        return {'PASS_THROUGH'}
        
    def invoke(self, context, event):
        return self.execute(context)

#------------------------------- Render Variables ------------------------------

class TMB_RenderVariables(TMB_Helpers, bpy.types.Operator):
    '''Render variables'''
    bl_idname = "tmb_render.variables"
    bl_label = "Render Variables"
    
    frames = []
    passes = []
    images = []
    frame = None
    subframe = None
    rendering_frame = None
    rendering_subframe = None
    started = None
    handler_complete = None
    handler_pre = None
    handler_final = None
    viewer = None
    timer = None
    final_completed = None
    skipped_frame = None
    
class TMB_RenderHelpers(TMB_RenderVariables, bpy.types.Operator):
    '''Render help functions'''
    bl_idname = "tmb_render.helpers"
    bl_label = "Render Helpers"
    
    op = None
    variables = None
    
    store = None
    project = None
    scenes = None
    rlayers = None
    render = None
    restore = None
    viewer = None
    viewer_image = None
    sc = None
    render_passes = None
    
    def structure(self):
        '''Sync to the main storage'''
        
        self.op = bpy.types.TMB_RENDER_OT_helpers
        self.variables = bpy.types.TMB_RENDER_OT_variables
        self.store = bpy.types.TMB_OT_store.store
        
        self.project = self.store['Project']
        self.scenes = self.store['Scenes']
        self.rlayers = self.store['RLayers']
        self.render = self.store['Render']
        self.restore = self.store['Restore']
        self.frames = self.render['frames']
        self.sc = self.project['main_sc']
        self.variables.timer = None
        self.variables.rendering_subframe = None
        self.variables.started = None
        self.variables.final_completed = None
        self.render_passes = self.project['render_passes']
        bpy.ops.tmb.update('INVOKE_DEFAULT')        
        self.viewer_image = bpy.data.images['Viewer Node']
        
        def _complete(self, context):
            '''subframe render_complete handler function'''
            
            _vars = bpy.types.TMB_RENDER_OT_variables
            _prj = bpy.types.TMB_OT_store.store['Project']
            _vars.rendering_subframe = False
            _vars.started = False
        
        def _pre(self, context):
            '''subframe render_pre handler function'''
            
            _vars = bpy.types.TMB_RENDER_OT_variables
            _vars.started = True
            
        def _final_complete(self, context):
            '''mixing frame render_complete handler function'''
            
            _vars = bpy.types.TMB_RENDER_OT_variables
            _vars.rendering_subframe = False
            _vars.final_completed = True
            _vars.started = False
                    
        self.handler_complete = _complete
        self.handler_pre = _pre
        self.handler_final = _final_complete
        while self.handler_complete in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(self.handler_complete)
        while self.handler_pre in bpy.app.handlers.render_pre:
            bpy.app.handlers.render_pre.remove(self.handler_pre)
        while self.handler_final in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_copmlete.remove(self.handler_final)
    
    def cleanup(self):
        '''Reset Operator variables'''
        
        self.op = None
        self.variables = None
        self.store = None
        self.project = None
        self.scenes = None
        self.rlayers = None
        self.render = None
        self.restore = None
        self.viewer = None
        self.viewer_image = None
        self.sc = None
        self.render_passes = None
        self.frames = []
        self.passes = []
        self.images = []
        self.frame = None
        self.subframe = None
        self.rendering_frame = None
        self.rendering_subframe = None
        self.rendering = None
        self.handler_complete = None
        self.handler_pre = None
        self.viewer = None
        self.timer = None
        self.skipped_frame = None
        bpy.types.TMB_OT_store.store = {}
    
    def finalize(self):
        '''Restore project settings'''
        
        if self.animation:
            bpy.ops.tmb.keyconfig()
        bpy.ops.tmb.restore()
    
    def get_frames(self): 
        '''Store list of frames into the self.render["frames"]'''
        
        sc = self.sc
        if self.animation:
            _start = sc.frame_start
            _end = sc.frame_end+1
            _step = sc.frame_step
            for fr in range(_start, _end, _step):
                self.frames.append(fr)
        else:
            self.frames.append(sc.frame_current)
    
    def get_subframes(self, sc):
        '''Calculate subframes for current frame in certain scene'''
        
        _tmb = sc.true_mb
        _position = _tmb.position
        _samples = _tmb.samples
        _shutter = round(_tmb.shutter/2, 3 )
        _frame = self.render['frame']
        #-------------------------start and end subframes from the TMB position:
        if _position == 'START':
            _start = _frame
            _end = _frame + _shutter*2
        elif _position == 'FRAME':
            _start = _frame - _shutter*2
            _end = _frame
        elif _position == 'CENTER':
            _start = _frame - _shutter
            _end = _frame + _shutter
        #----------------------------------------------------------storage sync:
        self.rlayers[sc]['subframes'] = []
        subframes = self.rlayers[sc]['subframes']
        conc_subframes = self.render['conc_subframes']
        #----------------------------------------------store the first subframe:
        subframes.append(_start) 
        if _start not in conc_subframes:
            conc_subframes.append(_start)
        #--------------------------------------if the number of samples is even:    
        if _samples % 2 == 0: 
            _step = (_end - _start) / (_samples - 1 )
            while round( (_start + _step), 4 ) <= _end:
                _start += _step
                _sub = round(_start, 4)
                subframes.append(_sub)
                if _sub not in conc_subframes:
                    conc_subframes.append(_sub)
        #---------------------------------------if the number of samples is odd:
        else: 
            _step = (self.frame - _start) / (_samples // 2 )
            while round( (_start + _step), 4 ) <= _end:
                _start += _step
                _sub = round(_start, 4)
                subframes.append(_sub)
                if _sub not in conc_subframes:
                    conc_subframes.append(_sub)
                    
    def set_frame(self):
        '''
        Pop frame from project['frames']
        Get subframes of the frame for all non-Cycles scenes with active TMB
        Store concatenated scenes subframes lists
            and store result into self.render['conc_subframes']
        '''
        
        self.frame = self.render['frames'].pop(0)
        self.render['frame'] = self.frame
        self.render['conc_subframes'] = []
        for sc in list(self.scenes.keys()):
            if (
                sc.render.engine != 'CYCLES' and
                sc.true_mb.activate and
                self.rlayers[sc] and
                self.rlayers[sc]['rlayers']
            ):
                sc.frame_set(self.frame, subframe = 0.0)
                self.get_subframes(sc)
                self.scenes[sc]['tmb']['position'] = sc.true_mb.position
                self.scenes[sc]['tmb']['shutter'] = sc.true_mb.shutter
                self.scenes[sc]['tmb']['samples'] = sc.true_mb.samples
                self.scenes[sc]['tmb']['boost'] = sc.true_mb.boost
                
            else:
                self.rlayers[sc]['subframes']= [self.frame]
        self.render['conc_subframes'].sort()
        self.render['conc_subframes'].append(self.frame) #------for final mixing
        
    def set_subframe(self):
        '''
        Pop subframe from self.render["conc_subframes"]
        Set it as current project subframe
        '''
        
        sc = self.sc
        self.render['subframe'] = self.render["conc_subframes"].pop(0)
        if self.render['subframe'] == self.render['frame']:
            if not self.skipped_frame:
                self.render["conc_subframes"].append(self.render['subframe'])
                self.render['subframe'] = self.render["conc_subframes"].pop(0)
                self.skipped_frame = True
            else:
                self.skipped_frame = False            
        _subfr = self.render['subframe']
        _fr = int(_subfr) #------------------------------------------- set frame
        _sbfr = round (_subfr - _fr, 3) #-------------------------- set subframe                
        for scene in list(self.rlayers.keys()):
            scene.frame_set(_fr, subframe=_sbfr) # -----------set current fr/sub
        for sc in list(self.rlayers.keys()):
            if (
                self.scenes[sc]['engine'] == 'CYCLES' or
                not self.scenes[sc]['tmb'] or
                not self.scenes[sc]['tmb']['activate']
            ):
                continue
            _rlayers = self.rlayers[sc]['rlayers']
            for rl in list(_rlayers.keys()):
                for npass in list(_rlayers[rl].keys()):
                    _fo = _rlayers[rl][npass]['file_output']
                    _path = _rlayers[rl][npass]['path']
                    _fo.base_path = pathlib.os.path.join(
                        _path, str(self.render['subframe'])
                    )
        
    def set_rlayers(self):
        '''
        Unmute TMB Render Layers if current subframe is in its scene's
            subframes list.
        '''
        
        self.images = []
        self.passes = []
        self.render['rlayers'] = []
        for sc in list(self.rlayers.keys()):
            _rlayers = self.rlayers[sc]['rlayers']            
            for rl in list(_rlayers.keys()):
                _mute = False
                # if this is the last subframe, which is only for non-TMB layers
                # or current subframe is not in this RL's scene subframes list:
                # mute Render Layer. Or unmute otherwise.
                if (
                    len(self.rlayers[sc]['subframes']) == 1 or
                    not self.render['subframe'] in self.rlayers[sc]['subframes']
                ):
                    _mute = True
                rl.mute = _mute
                            
                if (
                    self.scenes[sc]['engine'] == 'CYCLES' or
                    not self.scenes[sc]['tmb'] or
                    not self.scenes[sc]['tmb']['activate']
                ):
                    continue
                # if scene is non-Cycles, is TMB, and there are several scenes
                # with different TMB settings: mute or unmute TMB subframes
                # File Outputs depending on mute status of Render Layer
                else:
                    for npass in list(_rlayers[rl].keys()):
                        _rlayers[rl][npass]['file_output'].mute = _mute
                    
                if _mute:
                    continue
                
                # if Render Layer is not muted:
                _rl_sets = self.rlayers[sc]['rlayers'][rl]
                for npass in rl.outputs:
                    if (
                        npass.enabled and
                        npass in list(_rl_sets.keys())
                    ):
                        _img = _rl_sets[npass]['image']
                        self.images.append(_img)
                        self.passes.append(npass)
    
    def reset_images(self):
        '''Replace all temporary image pixels with numpy zeros arrays'''
        
        for img in self.render['images']:
            img.pixels[:] = np.zeros(self.project['pix_len'], dtype = 'f')[:]
            
    def timer_add(self, tick=0.01):
        '''Add timer event and set it as self.timer'''
        
        _wm = self.project['wm']
        _win = self.project['window']
        self.timer = _wm.event_timer_add(tick, window=_win)
    
    def timer_remove(self, vars=False):
        '''Remove timer event and clear self.timer'''
        
        _wm = self.project['wm']
        try:
            for _ in range(3):
                _wm.event_timer_remove(self.timer)
        except:
            pass
        self.timer = None
    
    def render_native(self):
        '''Native Blender render operator for instant renders'''
        
        bpy.ops.render.render(
            'INVOKE_DEFAULT',
            animation = self.animation,
            write_still = self.write_still,
            use_viewport = self.use_viewport,
            layer = self.layer,
            scene = self.scene
            )
    
    def render_subframe(self):
        '''Main TMB subframe render operator'''
        
        _vars = bpy.types.TMB_RENDER_OT_variables
        _vars.rendering_subframe = True
        bpy.ops.render.render(
            'INVOKE_DEFAULT',
            animation = False,
            write_still = False,
            use_viewport = self.use_viewport
        )
        
    def open_images(self, path):
        '''Open all subframe images files as images in Blender'''
        
        _fpath = pathlib.Path(path)
        images = []
        for child in _fpath.glob('*'):
            if child.is_file():
                img = bpy.data.images.load(str(child))
                images.append(img)
            else:
                images += self.open_images(str(child))
        return images
    
    def buffers_to_image(self, path, img, samples):
        '''Open subframe images, mix them to frame image and delete them'''
        
        _sub_images = self.open_images(path)
        _sub_arrays = np.zeros(
            (len(_sub_images), self.project['pix_len']),
            dtype = 'f'
        )
        for num in range(len(_sub_images)):
            _sub_arrays[num][:] = np.array(_sub_images[num].pixels[:])[:]
        _result = _sub_arrays.sum(axis=0)
        _divided = np.divide(_result[:], samples)
        img.pixels[:] = _divided[:]
        for img in _sub_images:
            bpy.data.images.remove(img)
    
    def delete_images(self, fpath):
        '''Delete all files in file path'''
        
        _fpath = pathlib.Path(fpath)
        for child in _fpath.glob('*'):
            if child.is_file():
                child.unlink()
            else:
                self.delete_images(child)
    
    def mix_buffers(self):
        '''Mix rendered subframes files to Blender images'''
        _scenes = self.rlayers
        for sc in list(_scenes.keys()):
            if (
                self.scenes[sc]['engine'] == 'CYCLES' or
                not self.scenes[sc]['tmb'] or
                not self.scenes[sc]['tmb']['activate']
            ):
                continue
            _rlayers = _scenes[sc]['rlayers']
            for rl in list(_rlayers.keys()):
                for npass in list(_rlayers[rl].keys()):
                    _path = _rlayers[rl][npass]['path']
                    _image = _rlayers[rl][npass]['image']
                    _samples = self.scenes[rl.scene]['tmb']['samples']
                    self.buffers_to_image(_path, _image, _samples)
                    self.delete_images(_path)
        
    def img_to_path(self):
        '''Move images from temp. File Output folder to scene render folder'''
        
        _dest = self.project['render_path'] #-----------------destination folder
        _tmp = self.project['path'] #---------------------------subframes folder
        _source = pathlib.os.path.join(_tmp, '_TMB_Output') #-------source folder
        _spath = pathlib.Path(_source)
        if not _spath.is_dir():
            for child in pathlib.Path(_tmp).glob('*'):
                if child.is_file() and '_TMB_Output' in str(child):
                    _new_name = str(child).replace( '_TMB_Output',
                                                self.project['base_name'])
                    child.rename(_new_name)
                    shutil.move(_new_name, _dest)
            return
        for child in _spath.glob('*'):
            if child.is_file():
                _new_name = str(child).replace( 'Image',
                                                self.project['base_name'])
                _check_path = _new_name.replace(str(_source), str(_dest))
                if pathlib.Path(_check_path).is_file():
                    pathlib.Path(_check_path).unlink()                        
                child.rename(_new_name)
                shutil.move(_new_name, _dest)
    
    def save_frame_prepare(self):
        '''Prepare project for frame saving'''
        
        _links = self.sc.node_tree.links
        #------------------------- mute all TMB render layers, unmute all others
        for rl in self.project['rlayers']:
            if (
                self.scenes[rl.scene]['tmb'] and
                self.scenes[rl.scene]['tmb']['activate']
            ):
                rl.mute = True
            else:
                rl.mute = False
        #--------------------------------------------- mute all TMB File Outputs
        for fo in self.restore['tmb_f_outs']:
            fo.mute = True
        #-------- relink all TMB images directly to TMB mix nodes children-links 
        if self.restore['mix_nodes']:
            for node in self.restore['mix_nodes']:
                for lnk in node.outputs[0].links:
                    _links.new( node.inputs[2].links[0].from_socket,
                                                lnk.to_socket)
        #------------------------------------------ unmute all user File Outputs
        if self.project['has_f_outs']:
            for fo in self.restore['file_outputs']:
                fo.mute = False
        #------------------------------- change render_copmlete handler function
        while self.handler_complete in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(self.handler_complete)
        bpy.app.handlers.render_complete.append(self.handler_final)
        #----------------------------------------- set current frame as subframe 
        _frame = self.render['conc_subframes'].pop(0)
        self.sc.frame_set(_frame, subframe = 0.0)
        #--------------------------- if render animation unmute main File Output
        if self.animation:
            self.project['output'].mute = False
        #------------------------------------------- update preview just in case
        bpy.ops.tmb.update('INVOKE_DEFAULT')
        
    def save_frame_restore(self):
        '''Restore project from frame saving'''
        
        _links = self.sc.node_tree.links
        self.sc.render.filepath = self.project['path']
        #------------------------------------------------- mute main File Output
        self.project['output'].mute = True
        #------------------------------------------------ mute user File Outputs
        if self.project['has_f_outs']:
            for fo in self.restore['file_outputs']:
                fo.mute = True
        #----------------- relink back all TMB images and mix (Alpha Over) nodes
        if self.restore['mix_nodes']:
            for node in self.restore['mix_nodes']:
                for lnk in node.inputs[2].links[0].from_socket.links:
                    if lnk.to_node == node:
                        continue
                    _links.new(node.outputs[0],lnk.to_socket)
        #---------------------------------------- umute all active Render Layers
        for rl in self.project['rlayers']:
            rl.mute = False
        #-------------------------------------------- umute all TMB File Outputs
        for fo in self.restore['tmb_f_outs']:
            fo.mute = False
        #------------------------------- change render_copmlete handler function
        while self.handler_final in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(self.handler_final)
        bpy.app.handlers.render_complete.append(self.handler_complete)
        #---------------- move rendered image file from main File Outputs folder
        #--------------------------------- to render folder (for animation only)
        self.img_to_path()
        #------------------------------------------- update preview just in case
        bpy.ops.tmb.update('INVOKE_DEFAULT')
    
    def instant(self, context):
        '''Check cases when it is possible to start native render instantly'''
        
        sc = context.scene
        _instant = False
        #----------------------------------------- if scene is Cycles or non-TMB
        if sc.render.engine == 'CYCLES' or not sc.true_mb.activate:
            #--------- if there's no node tree or no nodes or nodes are not used
            if not sc.node_tree or not sc.node_tree.nodes or not sc.use_nodes:
                _instant = True
            #---------------------- if there's node tree but all nodes are muted
            elif (
                sc.node_tree.nodes and 
                not [node for node in sc.node_tree.nodes if not node.mute]
                ):
                _instant = True
            #--------------------------- if there's node tree and nodes are used           
            elif sc.node_tree.nodes and sc.use_nodes:
                _instant = True
                #---------------- except there is active TMB scene in Compositor
                for node in sc.node_tree.nodes:
                    if (
                        node.type == 'R_LAYERS' and
                        not node.mute and
                        node.scene.render.engine != 'CYCLES' and
                        node.scene.true_mb.activate
                    ):
                        _instant = False
                        return _instant
        return _instant
    
    def instant_prepare(self, context):
        '''Prepare project for instant native render'''
        
        sc = context.scene
        if not sc.node_tree or not sc.node_tree.nodes:
            return
        #------------------------------- Turn off all TMB Mix (Alpha Over) nodes
        for node in sc.node_tree.nodes:
            if node.name.startswith('TMB_Mix') and node.type == 'ALPHAOVER':
                node.inputs[0].default_value = 0

#################################### RENDER ####################################
class TMB_Render(TMB_RenderHelpers, bpy.types.Operator):
    bl_idname = 'tmb_render.render'
    bl_label = 'Render'
    bl_description = 'Render active scene'
    animation : BoolProperty(
        name="Animation",
        description="Render Animation",
        default=False,
        )
    write_still : BoolProperty(
        name="Write Still",
        description="Write Still",
        default=False,
        )
    use_viewport : BoolProperty(
        name="Use viewport",
        description="Use Viewport",
        default=False,
        )
    layer : StringProperty(
        name="Render Layer",
        description="Render Layer",
        default="",
        )
    scene : StringProperty(
        name="Scene",
        description="Scene",
        default="",
        )

    def __init__(self):
        self.t1 = perf_counter()
    
    def __del__(self):
        #------------------------------ clear render handlers from TMB functions
        while self.handler_complete in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(self.handler_complete)
        while self.handler_pre in bpy.app.handlers.render_pre:
            bpy.app.handlers.render_pre.remove(self.handler_pre)
        while self.handler_final in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(self.handler_final)
        #--------------------------------------- reset TMB_Render Operator class
        self.cleanup()
        #------------------------------------ make report with total render time
        self.t2 = perf_counter()
        try:
            _total_time = str(datetime.timedelta(seconds=(self.t2-self.t1)))
            _msg = f'Total Render Time: {_total_time[:-3]}'
            bpy.ops.tmb.warning('INVOKE_DEFAULT', type = "INFO", msg = _msg)
        except:
            pass
                
    def execute(self, context):
        sc = context.scene
        if self.instant(context):
            self.instant_prepare(context)
            self.render_native()
            self.cleanup()
            return {'FINISHED'}
        self.cleanup()
        if sc.render.image_settings.file_format in (
                                            'AVI_JPEG', 'AVI_RAW', 'FFMPEG'):
            _msg = "Sorry!\nTrue Motion Blur currently doesn't support render\
 in\n\"AVI JPEG\", \"AVI Raw\" and \"FFmpeg video\" File Formats.\n\nPlease\
 change Output File Format in\nOutput Properties -> Output\n\nTip: If you need\
 to render animation, you may render image sequences."
            bpy.ops.tmb.warning('INVOKE_DEFAULT', type = 'ERROR', msg=_msg)
            return {'CANCELLED'}
        if not [obj for obj in sc.objects if obj.type == 'CAMERA']:
            _msg = f'Error: No camera found in scene "{sc.name}"'
            bpy.ops.tmb.warning('INVOKE_DEFAULT', type = 'ERROR', msg=_msg)
            return {'CANCELLED'}
        bpy.ops.tmb.setup(animation=self.animation)
        self.structure()
        if not self.project['composite'].inputs[0].links:
            bpy.ops.tmb.restore()
            _nt = self.sc.node_tree
            if '_TMB_Output' in _nt.nodes:
                _nt.nodes.remove(self.sc.node_tree.nodes['_TMB_Output'])
            _msg = "No Composite output. Can't render"
            bpy.ops.tmb.warning('INVOKE_DEFAULT', type = 'ERROR', msg=_msg)
            return {'FINISHED'}
        if not [rl for rl in self.project['rlayers'] if rl.scene.view_layers[rl.layer].use]:
            bpy.ops.tmb.restore()
            _nt = self.sc.node_tree
            if '_TMB_Output' in _nt.nodes:
                _nt.nodes.remove(self.sc.node_tree.nodes['_TMB_Output'])
            _msg = "All render layers are disabled for rendering"
            bpy.ops.tmb.warning('INVOKE_DEFAULT', type = 'ERROR', msg=_msg)
            return {'FINISHED'}
        self.get_frames()
        bpy.app.handlers.render_complete.append(self.handler_complete)
        bpy.app.handlers.render_pre.append(self.handler_pre)
        self.timer_add()
        self.project['wm'].modal_handler_add(self)
        return {"RUNNING_MODAL"}
    
    def modal(self, context, event):
        
        #------------------------------------------- if aborted by pressing ESC:
        if event.type == 'ESC':
            self.timer_remove()
            self.finalize()
            return {'CANCELLED'}
        #-------------------------------------------------- on each Timer event:
        elif event.type == 'TIMER':
            self.timer_remove() #---------------------------------- remove Timer
            _vars = bpy.types.TMB_RENDER_OT_variables
            
            #---- if subframe rendering haven't started after the first command:
            if _vars.rendering_subframe:
                if not _vars.started:
                    self.render_subframe()
            
            #---------------------------------------- if frame is not rendering:
            elif not self.rendering_frame:
                #------------------------ if there are no more frames to render:
                if not self.frames:
                    self.finalize()
                    return {'FINISHED'}
                #--------------------- otherwise reset TMB images, set frame and
                #------------------------ command to start rendering algorithms:
                else:
                    self.reset_images()
                    self.set_frame()
                    self.rendering_frame = True
            
            #--------------- if there's only one subframe (which is frame) left:
            elif len(self.render['conc_subframes']) == 1:
                #----------------- check if subframe rendering status is active:
                if not _vars.rendering_subframe:
                    _vars.rendering_subframe = True
                #---------------------- mix subframes to images, prepare saving,
                #--------------------------------------- and render mixed frame:
                self.mix_buffers()                
                self.save_frame_prepare()
                bpy.ops.render.render(
                    'INVOKE_DEFAULT',
                    animation = False,
                    write_still = False)
            
            #------- if render haven't started after previous command, force it:
            elif (
                not self.render['conc_subframes'] and
                not _vars.final_completed and
                not _vars.started
            ):
                self.render_subframe()
            
            #--------------------- if final subframe (frame) render is completed
            #----------------------------- set all command statuses as inactive:
            elif (
                not self.render['conc_subframes'] and
                _vars.final_completed
            ):
                _vars.final_completed = False
                self.save_frame_restore()                
                _vars.rendering_subframe = False
                self.rendering_frame = False
            #----------------- if subframe rendering is inactive, make it active
            #---------------- setup subframe and render layers and start render:
            elif not _vars.rendering_subframe:
                _vars.rendering_subframe = True
                self.set_subframe()
                self.set_rlayers()
                self.render_subframe()
            self.timer_add()#------------------------------------ add Timer back
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        return self.execute(context)
    
#--------------------------- For test purposes only ----------------------------

classes = [
    TMB_UpdatePreview,
    TMB_RenderVariables,
    TMB_RenderHelpers,
    TMB_Render, 
    ]    
    
def render_register():
    for cl in classes:
        register_class(cl)

def render_unregister():
    for cl in classes:
        unregister_class(cl)

if __name__ == '__main__':
    render_register()
