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
#  TMB render support operators
#  (c) 2020 Andrey Sokolov (so_records)

import bpy, pathlib, shutil
import numpy as np
from bpy.utils import register_class, unregister_class
from bpy.props import BoolProperty, StringProperty, EnumProperty, IntProperty

#------------------------------ Warning Operator -------------------------------

class TMB_Warning(bpy.types.Operator):
    '''Warning!'''
    bl_idname = "tmb.warning"
    bl_label = "Warning!"
    type: StringProperty()
    msg : StringProperty()
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        return {'FINISHED'}
    
    def modal(self, context, event):
        if event:
            self.report({self.type}, self.msg)
        return {'FINISHED'}
        
    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

############################## MAIN PROJECT STORAGE ############################

class TMB_Store(bpy.types.Operator):
    '''
    MAIN STORAGE
    Clear storage
    dict store {
        "Project": { #-------------------------------------Project constant info
            "context" : context
            "main_sc" : start scene blender path,
            "frame" : self.scene.frame_current,
            "wm" : context.window_manager,
            "window" : context.window,
            "path" : directory path to save animations,
            "format" : file format,
            "rlayers" : [ list of Render Layers nodes ],
            "composite" : composite output
            "output" : main file output
            "scenes" : [ list of scenes used for render ],
            "res_x" : x resolution
            "res_y" : y resolution
            "res_prc" : resolution percentage
            "pix_len" : int number of pixels per frame,
            "single" : True if main_sc.render.use_single_layer,
            "render_passes" : true_mb.render_passes,
            "has_f_outs" : True if compositor has active file outputs
            "links" : [ all active used Render Layers outputs ]
            "image_settings" : {
                "path" : _prj["main_sc"].render.filepath,
                "file_format" : _imgsets.file_format,
                "cineon_black" : _imgsets.cineon_black,
                "cineon_gamma" : _imgsets.cineon_gamma,
                "cineon_white" : _imgsets.cineon_white,
                "color_depth" : _imgsets.color_depth,
                "color_mode" : _imgsets.color_mode,
                "compression" : _imgsets.compression,
                "exr_codec" : _imgsets.exr_codec,
                "jpeg2k_codec" : _imgsets.jpeg2k_codec,
                "quality" : _imgsets.quality,
                "tiff_codec" : _imgsets.tiff_codec,
                "use_cineon_log" : _imgsets.use_cineon_log,
                "use_jpeg2k_cinema_48" : _imgsets.use_jpeg2k_cinema_48,
                "use_jpeg2k_cinema_preset" : _imgsets.use_jpeg2k_cinema_preset,
                "use_jpeg2k_ycc" : _imgsets.use_jpeg2k_ycc,
                "use_preview" : _imgsets.use_preview,
                "use_zbuffer" : _imgsets.use_zbuffer,
                "views_format" : _imgsets.views_format,
            }
        },
        "Scenes": { #----------------------Settings of the scenes used in render
            Scene 1: {
                "is_main" : True if scene is main scene,
                "engine" : sc.render.engine,
                "mb" : sc.eevee.use_motion_blur,*
                "samples" : sc.eevee.taa_render_samples.*
                "tmb" : { ** 
                    "activate" : true_mb.activate
                    "position" : true_mb.position
                    "shutter" : true_mb.shutter
                    "samples" : true_mb.samples
                    "boost" : true_mb.boost
                },
                ---------------------------
                * for Eevee TMB scenes
                ** for non-Cycles TMB scenes
            },
            Scene 2: {...{...},{...}...},
        },
        "Rlayers": { #------------------------------Render Layers used in render
            Scene 1 : {
                "rlayers" : {
                    RLayer1 : {
                            Pass1 : {
                                "index" : output index,
                                "links" : boolean,
                                "image" : pass image
                                "img_node" : pass image node,
                                "mix_node" : pass mix node,
                                "array" : ndarray for all subframes pixels
                                "file_output" : save buffer file output node
                                "path" : temporary save buffers directory
                            },
                            Pass2 : {...},
                            .....},                        
                    Rlayer2 : {...{...},{...},{...}},
                .....},
                "subframes" : [ list of subframes for current frame ]
            Scene 2 : {...{...},{...},{...}},
        .....},
        "Render": { #--------------------------------------Temporary render data
            "images" : [ tmb_images ],
            "frames" : [ frames to render ],
            "frame" : context frame,
            "conc_subframes" : [concatenated subframes from all scenes],
            "subframe" : context subframe,
            "rlayers" : [ not muted rlayers for current subframe ],
            "scene" : current rlayer scene,
            "rlayer" : current rlayer,
            "image" : current image,
            "npass" : current npass,
            "img_node" : if not render passes - TMB Image node,
            "mix_node" : if not render passes - TMB Mix node,
            "file_output" : if not render passes - file output,
            "path" : if not render passes - file output path 
        }
        "Restore": { #--------------------------------Data to process in the end
            "muted" : [ muted nodes to unmute when script is finished ],
            "deleted" : [ deleted viewers to recreate ],
            "tmb_nodes" : [ created nodes to delete when script is finished ],
            "main_dir" : main temporary directory (to delete),
            "mix_nodes" : [ list of TMB mix nodes ]
            "folders" : [ temporary folders created by script in main_dir ],
            "area" : { area : type }
            "file_outputs" : [ list of user file outputs ]
            "tmb_f_outs" : [ list of tmb file outputs ]
            "viewers" : {
                V1.name : {
                    "center_x" : node.center_x,
                    "center_y" : node.center_y,
                    "color" : node.color,
                    "height" : node.height,
                    "hide" : node.hide,
                    "label" : node.label,
                    "location" : node.location,
                    "mute" : node.mute,
                    "name" : node.name,
                    "show_options" : node.show_options,
                    "show_preview" : node.show_preview,
                    "show_texture" : node.show_texture,
                    "use_alpha" : node.use_alpha,
                    "use_custom_color" : node.use_custom_color,
                    "width" : node.width,
                    "width_hidden" : node.width_hidden,
                    "inputs" : {
                        In 1.name : {
                            "type" : input.type,
                            "name" : input.name,
                            "identifier" : input.identifier,
                            "enabled" : input.enabled,
                            "hide" : input.hide,
                            "links" : input.links[0].from_socket
                        },
                        In2.name : {....},
                    ...}                            
                ...},
                V2.name : {...},
            ...},
        },
    }
    Set context scene as "main_sc"
    '''
    
    bl_idname = "tmb.store"
    bl_label = "Storage"
    bl_description = "Project storage"
    animation : BoolProperty(
        name="Animation",
        description="Render Animation",
        default=False,
        )
    op = None
    store = {}
    scene = None
    enable = False
    
    def structure(self):
        '''Setup main storage common structure'''
        
        op = self.op
        op.store = {}
        op.store["Project"] = {}
        op.store["RLayers"] = {}
        op.store["Scenes"] = {}
        op.store["Render"] = {}
        _render = op.store["Render"]
        _render["images"] = []
        _render["frames"] = []
        _render["frame"] = None
        _render["rlayers"] = []
        _render["conc_subframes"] = []
        _render["subframe"] = None
        _render["file_output"] = None
        op.store["Restore"] = {}
        _restore = op.store["Restore"]
        _restore["muted"] = []
        _restore["file_outputs"] = []
        _restore["tmb_f_outs"] = []
        _restore["viewers"] = {}
        _restore["tmb_nodes"] = []
        _restore["main_dir"] = None
        _restore["mix_nodes"] = []
        _restore["folders"] = []
        _restore["area"] = {}
    
    def single(self):
        '''
        Get and set or create basic Compositor node setup:
        Single Render Layers and Composite nodes.
        Make sure they are connected.
        '''
        
        _scene = self.scene
        _nodes = _scene.node_tree.nodes
        _links = _scene.node_tree.links
        _rl_name = 'TMB Render Layers'
        _c_name = 'TMB Composite'
        _rl_node = (
            _nodes.new(type='CompositorNodeRLayers')
            if _rl_name not in _nodes else
            _nodes[_rl_name]
        )
        _c_node = (
            _nodes.new(type='CompositorNodeComposite')
            if _c_name not in _nodes else
            _nodes[_c_name]
        )
        self.store['Project']["composite"] = _c_node
        _rl_node.mute = False
        _c_node.mute = False
        _rl_node.name = _rl_name        
        _c_node.name = _c_name
        self.store['Restore']['tmb_nodes'].append(_rl_node)
        self.store['Restore']['tmb_nodes'].append(_c_node)
        _links.new( _rl_node.outputs[0], _c_node.inputs[0] )
        _c_node.location.x = _rl_node.location.x + 500
        _c_node.location.y = _rl_node.location.y
        
    def mute_all(self):
        '''Mute all unmuted nodes in the main scene's Compositor'''
        
        nodes = self.scene.node_tree.nodes
        for node in nodes:    
            if not node.mute:
                node.mute = True
                if node.type == 'COMPOSITE':
                    self.store['Restore']['muted'].append(node)
    
    def get_rlayers_and_scenes(self):
        '''
        Return:
          a list of all unmuted Render Layers in the main scene's Compositor
          a list of all scenes used in the main scene's Compositor
        '''
        
        sc = self.scene
        _scenes = [sc,]
        _rlayers = []
        if not sc.node_tree:
            sc.use_nodes = True
        elif not sc.node_tree.nodes:
            sc.use_nodes = True
            self.single()
        elif not sc.use_nodes and sc.node_tree.nodes:
            sc.use_nodes = True
            self.mute_all()
            self.single()
        _nodes = sc.node_tree.nodes
        for node in _nodes:
            if (
                node.type == 'R_LAYERS' and
                not node.mute and
                node.scene.view_layers[node.layer].use
            ):
                _rlayers.append(node)
                if node.scene not in _scenes:
                    _scenes.append(node.scene)
        return _rlayers, _scenes
    
    def get_pixels_len(self):
        '''Return the main scene's number of pixels'''
        
        op = self.op
        sc = self.scene
        _prj = op.store['Project']
        _prj["res_x"] = sc.render.resolution_x
        _prj["res_y"] = sc.render.resolution_y
        _prj["res_prc"] = sc.render.resolution_percentage
        _resX =  _prj['res_x']
        _resY =  _prj['res_y']
        _resPrc =  _prj['res_prc']
        _pixels = (int(_resX*(_resPrc/100)) * int(_resY*(_resPrc/100)) * 4)
        return _pixels
    
    def get_render_passes(self):
        '''
        Return True if there is at least one non-Cycles scene
        in the main scene's Compositor setup
        with enabled TMB and Render Passes options
        '''
        
        op = self.op
        sc = self.scene
        _proj = op.store['Project']
        _render_passes = False
        if sc.render.engine != 'CYCLES' and sc.true_mb.activate:
            _render_passes = sc.true_mb.render_passes
        elif (
            len(_proj['rlayers']) > 1 and
            len(_proj['scenes']) > 1
        ):
            for scene in  _proj['scenes']:
                if (
                    scene.render.engine != 'CYCLES' and
                    scene.true_mb.activate and
                    not _render_passes
                ):
                     _render_passes = sc.true_mb.render_passes
        return _render_passes
    
    def get_composite(self):
        '''
        Find the main scene Compositor's Composite node.
        Return the first one found or None if not found at all.
        '''
        
        sc = self.scene
        _composite = None
        if sc.node_tree and sc.node_tree.nodes and sc.use_nodes:
            nodes = sc.node_tree.nodes        
            for node in nodes:
                if node.type == 'COMPOSITE' and not node.mute:
                    _composite = node
                    break
        return _composite
    
    def project(self, context):
        '''
        Setup the main storage "Project" dictionary.
        Contains the common information about the whole project.
        '''
        
        op = self.op
        _prj = op.store['Project']
        _prj["context"] = {
            "window" : context.window,
            "screen" : context.screen,
            "area" : context.area,
            "region" : context.region,
        }
        _prj["main_sc"] = context.scene
        self.scene = _prj['main_sc']
        _prj["frame"] = self.scene.frame_current
        _prj["wm"] = context.window_manager
        _prj["window"] = context.window
        _prj["user_path"] = self.scene.render.filepath
        _prj["base_name"] = bpy.path.display_name_from_filepath(
                                                            _prj["user_path"]
                                                            )
        if not _prj["base_name"]:
            _prj["path"] = bpy.path.abspath(_prj["user_path"])
        else:
            _prj["path"] = bpy.path.abspath(
                str(_prj["user_path"]).replace(
                    _prj["base_name"], ""
                    )
            )
        _prj["format"] = self.scene.render.image_settings.file_format
        _rlscenes = self.get_rlayers_and_scenes()
        _prj["rlayers"] = _rlscenes[0]
        _prj["composite"] = self.get_composite()
        _prj["output"] = None
        _prj["scenes"] = _rlscenes[1]
        _prj["pix_len"] = self.get_pixels_len()
        _prj["single"] = context.scene.render.use_single_layer
        _prj["render_passes"]= self.get_render_passes()
        _prj["has_f_outs"] = False
        _prj["links"] = []
        _imgsets = _prj["main_sc"].render.image_settings
        _prj["image_settings"] = {
            "path" : _prj["main_sc"].render.filepath,
            "file_format" : _imgsets.file_format,
            "cineon_black" : _imgsets.cineon_black,
            "cineon_gamma" : _imgsets.cineon_gamma,
            "cineon_white" : _imgsets.cineon_white,
            "color_depth" : _imgsets.color_depth,
            "color_mode" : _imgsets.color_mode,
            "compression" : _imgsets.compression,
            "exr_codec" : _imgsets.exr_codec,
            "jpeg2k_codec" : _imgsets.jpeg2k_codec,
            "quality" : _imgsets.quality,
            "tiff_codec" : _imgsets.tiff_codec,
            "use_cineon_log" : _imgsets.use_cineon_log,
            "use_jpeg2k_cinema_48" : _imgsets.use_jpeg2k_cinema_48,
            "use_jpeg2k_cinema_preset" : _imgsets.use_jpeg2k_cinema_preset,
            "use_jpeg2k_ycc" : _imgsets.use_jpeg2k_ycc,
            "use_preview" : _imgsets.use_preview,
            "use_zbuffer" : _imgsets.use_zbuffer,
            "views_format" : _imgsets.views_format,
        }
        
    def scenes(self):
        '''
        Setup the main storage "Scenes" dictionary.
        Contains necessary information about the settings of all scenes
        used in the main scene's Compositor. 
        '''
        
        op = self.op
        for sc in op.store['Project']['scenes']:
            op.store['Scenes'][sc] = {}
            _sets = op.store['Scenes'][sc]
            _sets["is_main"] = True if sc is self.scene else False
            _sets["engine"] = sc.render.engine
            if _sets['engine'] == 'BLENDER_EEVEE' and sc.true_mb.activate:
                _sets["samples"] = sc.eevee.taa_render_samples
                _sets["mb"] = sc.eevee.use_motion_blur
            if _sets['engine'] != 'CYCLES' and sc.true_mb.activate:
                _sets["tmb"] = {
                    "activate" : sc.true_mb.activate,
                    "position" : sc.true_mb.position,
                    "shutter" : sc.true_mb.shutter,
                    "samples" : sc.true_mb.samples,
                    "boost" : sc.true_mb.boost
                }
            else:
                _sets["tmb"] = False
    
    def execute(self, context):
        self.op = bpy.types.TMB_OT_store
        self.structure()
        self.project(context)
        self.scenes()
        return {'FINISHED'}
    
################################### PREPARE ####################################

#------------------------------- Check Passes ----------------------------------

class TMB_Helpers():
    '''Helper methods for multiple scenes render without TMB render passes'''
        
    def npass_used(self, npass, node_type = 'COMPOSITE'):
        '''
        Check if npass's links lead to an active Composite or File Output node
        npass == node pass (node output in other words)
        Return True or False
        '''
        
        if not len(npass.links):
            return False
        else:
            for lnk in npass.links:
                _child = lnk.to_node
                _used = False
                if _child.type == 'COMPOSITE' and not _child.mute:
                    return True
                elif (
                    _child.type == node_type == 'OUTPUT_FILE' and
                    _child in list(self.restore['file_outputs'].keys())
                ):
                    return True
                # there's no need to check if outputs don't exist at all
                # because in this case they are represented as an empty list,
                # not None
                for out in _child.outputs:
                    _used = self.npass_used(out, node_type=node_type)
                    if not _used:
                        continue
                    return _used
    
    def clear_path(self, fpath):
        '''Remove directory and all its content'''
        
        _fpath = pathlib.Path(fpath)
        for child in _fpath.glob('*'):
            if child.is_file():
                child.unlink()
            else:
                self.clear_path(child)
        _fpath.rmdir()
    
#-------------------------------- Get Rlayers ----------------------------------  
  
class TMB_RLayers(TMB_Helpers, bpy.types.Operator):
    '''
    Collect main scene Compositor's Render Layers nodes' passes info
    or create Render Layers from scratch if none exists
    '''
    
    bl_idname = 'tmb.rlayers'
    bl_label = 'Get Render Layers'
    store = None
    project = None
    scenes = None
    restore = None
    scene = None
    advanced = None
    render_passes = None    
    
    def structure(self):
        '''Sync to the main storage'''
        
        self.store = bpy.types.TMB_OT_store.store
        self.project = self.store['Project']
        self.scenes = self.store['Scenes']
        self.restore = self.store['Restore']
        self.scene = self.project['main_sc']
        self.render_passes = self.project['render_passes']

    def get_layers_passes(self):
        '''Collect passes info for all main scene Compositor's Render Layers'''
    
        _rlayers = {}
        for rl in self.project['rlayers']:
            _rlayers[rl] = {}
            for out in range(len(rl.outputs)):
                if (
                    not self.render_passes and
                    not self.project['image_settings']['file_format'] ==
                                                    'OPEN_EXR_MULTILAYER' and
                    not self.npass_used(rl.outputs[out])
                ):
                    continue
                npass = rl.outputs[out]
                if npass.enabled:
                    _rlayers[rl][npass] = {}
                    _rlayers[rl][npass]["index"] = out
                    _rlayers[rl][npass]["links"] = (
                        True if npass.links else False
                    )
        return _rlayers
    
    def get_scenes_rlayers(self):
        '''
        Collect main scene Compositor's Render Layers passes info for each scene
        used in the main scene Compositor's Render Layers'''
        
        _rlayers = self.get_layers_passes()
        _rdict = {}
        for sc in self.project['scenes']:
            _rdict[sc] = {}
            _rdict[sc]["rlayers"] = {}
            _rdict[sc]["subframes"] = []
            for rl in list(_rlayers.keys()):
                if rl.scene == sc:
                    _rdict[sc]["rlayers"][rl] = _rlayers[rl]
        return _rdict
    
    def rlayers(self):
        '''
        Store main scene Compositor's Render Layers info into the main storage:
        RL Scene 1 : {
            "subframes" : [],
            "rlayers" : {
                RL 1 : {
                    Pass 1 : {
                        "index" : Pass 1 index,
                        "links" : True if Pass 1 has links,
                    },
                    Pass 2: {...},
                },
                RL 2 : { "passes" : {{...},{...},{...}}
            },
        },
        RL Scene 2 : {... ...},
        '''
        self.store['RLayers'] = self.get_scenes_rlayers()
    
    def execute(self, context):
        self.structure()
        self.rlayers()
        return {'FINISHED'}
    
#----------------- Mute user File Outputs and delete Viewers -------------------

class TMB_UserOutputs(bpy.types.Operator):
    '''Mute file outputs and remove viewers'''
    
    bl_idname = "tmb.userouts"
    bl_label = "User Outputs"
    store = None
    project = None
    restore = None
    rlayers = None
    f_outputs = None
    viewers = None
    scene = None
    rl_links = []
    
    def structure(self):
        '''Sync to the main storage'''
        
        self.store = bpy.types.TMB_OT_store.store
        self.project = self.store['Project']
        self.restore = self.store['Restore']
        self.rlayers = self.store['RLayers']
        self.f_outputs = self.restore['file_outputs']
        self.viewers = self.restore['viewers']
        self.scene = self.project['main_sc']
        self.rl_links = []
        
    def has_links(self, node):
        '''Return False if there's no input links to node, True otherwise'''
        
        _links = False
        for input in node.inputs:
            if input.links:
                _links = True
                break
        return _links
    
    def links_from_rl(self, input):
        '''Append to "self.rl_links" any links to Render Layer nodes' outputs'''
        
        if not input.links:
            return False
        elif (
            input.links[0].from_node.type == 'R_LAYERS' and
            not input.links[0].from_node.mute
        ):
            _rl = input.links[0].from_node
            _rl_dict = self.rlayers[_rl.scene]['rlayers'][_rl]
            _rl_dict[input.links[0].from_socket] = {}
            return True
        elif not input.links[0].from_node.inputs:
            return False
        else:
            for i in input.links[0].from_node.inputs:
                if self.links_from_rl(i):
                    return True
            return False
    
    def get_rl_links(self, node):
        if not node.inputs or not self.has_links(node):
            return False
        for num in range(len(node.inputs)):
            input = node.inputs[num]            
            if self.links_from_rl(input):
                return True
        return False
        
    def outputs(self):
        '''
        Store and mute user File Outputs in the main scene Compositor.
        Collect info about Viewer nodes in the main scene Compositor
        to recreate them on Restore step - and delete them.
        This is needed because Blender Viewers' behavior is pretty
        unpredictable and the only way to make sure render results
        are displayed correctly is to delete Viewer and to create it back then. 
        Just muting or unlinking unfortunately is not always a solution
        '''
        
        sc = self.scene
        nodes = sc.node_tree.nodes
        for node in nodes:                           
            if node.type == 'OUTPUT_FILE' and not node.mute:
                if self.get_rl_links(node):                    
                    if not self.project['has_f_outs']:
                        self.project['has_f_outs'] = True
                    self.f_outputs.append(node)
                    node.mute = True
                    self.restore['muted'].append(node)
            elif node.type == 'VIEWER':
                self.viewers[node.name] = {
                    "center_x" : node.center_x,
                    "center_y" : node.center_y,
                    "color" : node.color,
                    "height" : node.height,
                    "hide" : node.hide,
                    "label" : node.label,
                    "location" : node.location,
                    "mute" : node.mute,
                    "name" : node.name,
                    "show_options" : node.show_options,
                    "show_preview" : node.show_preview,
                    "show_texture" : node.show_texture,
                    "use_alpha" : node.use_alpha,
                    "use_custom_color" : node.use_custom_color,
                    "width" : node.width,
                    "width_hidden" : node.width_hidden,
                }
                self.viewers[node.name]["inputs"] = {}
                inputs = self.viewers[node.name]["inputs"]
                for input in node.inputs:
                    inputs[input.name] = {}
                    inputs[input.name]["type"] = input.type
                    inputs[input.name]["name"] = input.name
                    inputs[input.name]["identifier"] = input.identifier
                    inputs[input.name]["enabled"] = input.enabled
                    inputs[input.name]["hide"] = input.hide
                    inputs[input.name]["links"] = (
                        None if not input.links else
                        input.links[0].from_socket
                    )
                self.restore['deleted'] = node.name
                nodes.remove(node)
        
    def execute(self, context):
        self.structure()
        self.outputs()
        return {'FINISHED'}

#----------------- Get all Render Layers used active outputs -------------------

class TMB_Links(TMB_Helpers, bpy.types.Operator):
    '''Get active outputs'''
    bl_idname = 'tmb.links'
    bl_label = 'Get Links'
    store = None
    project = None
    
    def structure(self):
        '''Sync to the main storage'''
        
        self.store = bpy.types.TMB_OT_store.store
        self.project = self.store['Project']
        self.scenes = self.store['Scenes']
        self.restore = self.store['Restore']
        self.render_passes = self.project['render_passes']    
        self.links = self.project['links']
        self.rl_links = []
        
    def get_connected_rl_outs(self, input):
        '''
        Check if File Output input's links lead to active Render Layers' pass
        Append pass to self.rl_links if found
        '''
        
        if not input.links:
            return
        elif (
            input.links[0].from_node.type == 'R_LAYERS' and
            not input.links[0].from_node.mute
        ):
            self.rl_links.append(input.links[0].from_socket)
        elif not input.links[0].from_node.inputs:
            return
        else:
            for i in input.links[0].from_node.inputs:
                self.get_connected_rl_outs(i)
            return
    
    def get_all_links(self):
        '''
        Collect all active Render Layers' outputs to the self.links list
        '''
        
        # Collect all npasses leading to Composite
        for rl in self.project['rlayers']:
            if (
                self.scenes[rl.scene]['engine'] == 'CYCLES' or
                not self.scenes[rl.scene]['tmb'] or
                not self.scenes[rl.scene]['tmb']['activate'] or
                not rl.scene.view_layers[rl.layer].use
            ):                
                continue
            
            # if RL-scene is non-Cycles, TMB is on and RL is used for rendering: 
            for num in range(len(rl.outputs)):
                if (
                    not rl.outputs[num].enabled or 
                    (
                    not self.render_passes and
                    not self.project['image_settings']['file_format'] ==
                                                    'OPEN_EXR_MULTILAYER' and
                    not self.npass_used(rl.outputs[num])
                    )
                ):
                    continue                
                else:
                    # if npass is enabled and used for rendering
                    # or TMB Render Passes is on
                    self.links.append(rl.outputs[num])        
        
        # Collect all npasses leading to the user active File Outputs        
        if not self.project['has_f_outs']:
            return
        
        # Execute only if user File Outputs exist        
        _fouts = self.restore['file_outputs']
        for fo in _fouts:
            for input in fo.inputs:
                if not input.links:
                    continue
                self.rl_links = []
                self.get_connected_rl_outs(input)
                if not self.rl_links:
                    continue
                for lnk in self.rl_links:
                    if lnk not in self.links:
                        self.links.append(lnk)
                self.rl_links = []
                
    def execute(self, context):
        self.structure()
        self.get_all_links()
        return {'FINISHED'}
    
#------------------- Add File Outputs for saving subframes ---------------------

class TMB_SaveBuffers(TMB_Helpers, bpy.types.Operator):
    '''Add Save Buffers File Outputs'''
    
    bl_idname = 'tmb.savebuffers'
    bl_label = 'Save Buffers'
    store = None
    project = None
    scenes = None
    render_passes = None
    rlayers = None
    restore = None
    scene = None
    links = None
    
    def structure(self):
        '''Sync to the main storage'''
        
        self.store = bpy.types.TMB_OT_store.store
        self.project = self.store['Project']
        self.scenes = self.store['Scenes']
        self.render_passes = self.project['render_passes']
        self.rlayers = self.store['RLayers']
        self.restore = self.store['Restore']
        self.scene = self.project['main_sc']
        self.links = self.project['links']
    
    def get_fo(self, fo_name):
        '''Create/use existing TMB File Output for saving buffers'''
        
        sc = self.scene
        _fo = ( sc.node_tree.nodes.new('CompositorNodeOutputFile')
            if fo_name not in sc.node_tree.nodes else
            sc.node_tree.nodes[fo_name]
        )
        _fo.name = fo_name
        _fo.mute = False
        if _fo not in self.restore['tmb_nodes']:
            self.restore['tmb_nodes'].append(_fo)
        if _fo not in self.restore['tmb_f_outs']:
            self.restore['tmb_f_outs'].append(_fo)
        return _fo
    
    def add_main_dir(self):
        '''
        Create main temporary directory in the project render folder.
        Store it into the main storage
        '''
        
        _proj_dir = self.project['path']
        if (
            not pathlib.os.path.exists(_proj_dir) or
            pathlib.os.path.isfile(_proj_dir)
        ):
            _proj_dir = pathlib.Path(str(_proj_dir))
            _proj_dir = str(_proj_dir.parents[0])
        _tmb_dir = pathlib.os.path.join(_proj_dir, "_True_Motion_Blur_tmp")
        _main_out = pathlib.os.path.join(_proj_dir, 'TMB_Output')
        if pathlib.os.path.exists(_tmb_dir):
            self.clear_path(_tmb_dir)
        if  pathlib.os.path.exists(_main_out):
            self.clear_path(_main_out)
        pathlib.Path(_tmb_dir).mkdir(parents=True, exist_ok=True)
        self.restore["main_dir"] = _tmb_dir
    
    def get_path(self, sc_name, vl_name, out_index):
        '''
        Create File Output folder (individual for each pass)
        and store it to the main storage
        '''
        
        main_dir = self.restore['main_dir']
        fo_path = pathlib.os.path.join(
            main_dir, sc_name, vl_name, str(out_index)
        )
        pathlib.Path(fo_path).mkdir(parents=True, exist_ok=True)
        self.restore['folders'].append(fo_path)
        return fo_path
    
    def save_buffers_add(self):
        '''Create, setup and link File Outputs for each active render pass'''
    
        sc = self.scene
        _links = sc.node_tree.links
        _f_outs = self.restore['file_outputs']
        y_loc = 0
        for lnk in self.links:
            y_loc += 1
            _rl = lnk.node
            _num = [
                out for out in range(len(_rl.outputs))
                if _rl.outputs[out] == lnk
                ][0]
            _fo_name = f'{_rl.scene.name}_{_rl.layer}_{_num:02d}'
            _fo = self.get_fo(_fo_name)
            _fo.base_path = self.get_path(_rl.scene.name, _rl.layer, _num)
            _fo.format.file_format = "OPEN_EXR"
            _fo.format.color_mode = "RGB"
            _fo.format.color_depth = "32"
            _fo.location.x = _rl.location.x + 300
            _fo.location.y = _rl.location.y + 300 - (22 * y_loc)
            _fo.hide = True
            _links.new(lnk,_fo.inputs[0])
            
            _sets = self.rlayers[_rl.scene]['rlayers'][_rl][_rl.outputs[_num]]
            _sets["file_output"] = _fo
            _sets["path"] = _fo.base_path
                
    def output_fo_add(self):
        '''Add main File Output which will act as a render result writer'''
        
        _imgsets = self.project['image_settings']
        _fo = self.get_fo("TMB_Output")
        self.restore['tmb_f_outs'].remove(_fo)
        self.project['output'] = _fo
        _frm = _fo.format
        
        _fo.base_path = pathlib.os.path.join(self.project['path'],'TMB_Output')
        _frm.file_format = _imgsets["file_format"]
        if _imgsets["cineon_black"]:
            _frm.cineon_black = _imgsets["cineon_black"]
        if _imgsets["cineon_gamma"]:
            _frm.cineon_gamma = _imgsets["cineon_gamma"]
        if _imgsets["cineon_white"]:
            _frm.cineon_white = _imgsets["cineon_white"]
        if _imgsets["color_depth"]:
            _frm.color_depth = _imgsets["color_depth"]
        if _imgsets["color_mode"]:
            _frm.color_mode = _imgsets["color_mode"]
        if _imgsets["compression"]:
            _frm.compression = _imgsets["compression"]
        if _imgsets["exr_codec"]:
            _frm.exr_codec = _imgsets["exr_codec"]
        if _imgsets["jpeg2k_codec"]:
            _frm.jpeg2k_codec = _imgsets["jpeg2k_codec"]
        if _imgsets["quality"]:
            _frm.quality = _imgsets["quality"]
        if _imgsets["tiff_codec"]:
            _frm.tiff_codec = _imgsets["tiff_codec"]
        if _imgsets["use_cineon_log"]:
            _frm.use_cineon_log = _imgsets["use_cineon_log"]
        if _imgsets["use_jpeg2k_cinema_48"]:
            _frm.use_jpeg2k_cinema_48 = _imgsets["use_jpeg2k_cinema_48"]
        if _imgsets["use_jpeg2k_cinema_preset"]:
            _frm.use_jpeg2k_cinema_preset = _imgsets["use_jpeg2k_cinema_preset"]
        if _imgsets["use_jpeg2k_ycc"]:
            _frm.use_jpeg2k_ycc = _imgsets["use_jpeg2k_ycc"]
        _frm.use_preview = _imgsets["use_preview"]
        _frm.use_zbuffer = _imgsets["use_zbuffer"]
        _frm.views_format = _imgsets["views_format"]
        
        if not self.project['composite'].inputs[0].links:
            # If there's no active connected Composite node the whole operation
            # will be aborted from the main render operator right after setup
            return
        
        _to_mix = self.project['composite'].inputs[0].links[0].from_socket
        self.scene.node_tree.links.new(_to_mix, _fo.inputs[0])
        if _imgsets['file_format'] == 'OPEN_EXR_MULTILAYER':
            for lnk in self.links:
                _new_in = _fo.layer_slots.new(name = lnk.name)
                self.scene.node_tree.links.new(lnk, _new_in)
        _fo.mute = True
        
    def execute(self, context):
        self.structure()
        self.add_main_dir()
        self.save_buffers_add()
        self.output_fo_add()
        return {'FINISHED'}
    
#------------------------- Get TMB Mix and Image nodes -------------------------

class TMB_AddMixImages(TMB_Helpers, bpy.types.Operator):
    '''
    Generate Blender Images to store render results to. Add Alpha Over nodes
    to control wether Render Layers or Images will be used for render output'''
    bl_idname = "tmb.miximgs"
    bl_label = "Mix and Images"
    store = None
    project = None
    scenes = None
    render_passes = None
    rlayers = None
    render = None
    restore = None
    links = None
    i_name = ""
    m_name = ""
    scene = None
    
    def structure(self):
        '''Sync to the main storage'''
        
        self.store = bpy.types.TMB_OT_store.store
        self.project = self.store['Project']
        self.scenes = self.store['Scenes']
        self.rlayers = self.store['RLayers']
        self.restore = self.store['Restore']
        self.render = self.store['Render']
        self.scene = self.project['main_sc']
        self.render_passes = self.project['render_passes']
        self.links = self.project['links']
        self.i_name = "TMB_Image"
        self.m_name = "TMB_Mix"
    
    def remove_existing(self):
        '''
        Find and delete previously created TMB Images and Mix (Alpha Over) nodes
        '''
        
        sc = self.scene
        _links = sc.node_tree.links
        for node in sc.node_tree.nodes:
            # For mix nodes - reconnect neighbour nodes and delete mix nodes
            if (
                node.name.startswith(self.m_name) and
                node.type == 'ALPHAOVER'
            ):
                _in_links = node.inputs[1].links
                
                if (
                    _in_links and
                    (
                    _in_links[0].from_node.type == 'R_LAYERS' or
                    node.name == self.m_name
                    )
                ):
                    _out_links = node.outputs[0].links
                    _in_links = node.inputs[1].links
                    if _out_links and _in_links:
                        for lnk in _out_links:
                            _links.new(_in_links[0].from_socket, lnk.to_socket)
                sc.node_tree.nodes.remove(node)
            # For Image nodes - delete them
            elif (
                node.name.startswith(self.i_name) and
                node.type == 'IMAGE'
            ):
                sc.node_tree.nodes.remove(node)
    
    def get_image(self, i_name):
        '''
        Generate and return Blender Image
        or update settings if it already exists
        '''
        
        sc = self.scene
        prj = self.project
        _images = bpy.data.images
        _res_x = int(prj['res_x']*(prj['res_prc']/100))
        _res_y = int(prj['res_y']*(prj['res_prc']/100))
        
        # if image exists:
        if i_name in _images:
            
            # if existing image pixel number is different from project's:
            if _images[i_name].pixels-self.project['pix_len']:
                _images.remove(_images[i_name])
                _img = _images.new(i_name, _res_x, _res_y)
                
            # if existing image pixel number is the same as project's:
            else: 
                _img = _images[i_name]
        else:
            _img = _images.new(i_name, _res_x, _res_y)
            
        _img.file_format = 'OPEN_EXR'
        _img.use_generated_float = True
        return _img
    
    def add_mix_img(self):
        ''''Return new Image and new Alpha Over node'''
        
        nodes = self.scene.node_tree.nodes
        i_node = nodes.new('CompositorNodeImage')
        m_node = nodes.new('CompositorNodeAlphaOver')
        return i_node, m_node
    
    def set_mix_node(self, m_node, rl, npass, y_loc):
        '''Setup and return mix node: name, location, hide, reconnect links'''
    
        _links = self.scene.node_tree.links
        m_name = self.get_name('mix', rl, npass)
        m_node.name = m_name
        m_node.location.x = rl.location.x + 260
        m_node.location.y = rl.location.y - 22 * y_loc - 4
        m_node.inputs[0].default_value = 0
        m_node.hide = True
        m_node.use_premultiply = True
        if npass.links:
            for lnk in npass.links:
                _links.new(m_node.outputs[0], lnk.to_socket)
        return m_node
    
    def set_image(self, i_name):
        '''
        Find/add Blender generated image (make sure an image number
        of pixels matches the scene number of pixels). Assign numpy
        zeros array as Image pixels. Return Image.
        '''
        
        images = bpy.data.images
        if (
            i_name in images and
            len(images[i_name].pixels) != self.project['pix_len']
        ):
            images.remove(images[i_name])
        i_image = (
            self.get_image(i_name)
            if i_name not in images else
            images[i_name]
        )
        return i_image

    def set_img_node(self, i_node, i_image, m_node):
        '''Setup and return Image node: name, location, hide, Image'''
    
        i_name = i_image.name
        i_node.name = i_name
        i_node.image = i_image
        i_node.location.x = m_node.location.x - 410
        i_node.location.y = m_node.location.y - 15
        i_node.hide = True
        return i_node
    
    def get_name(self, type, rl, npass):
        '''
        Generate a name based on the node type, scene,
        view layer and the render pass
        '''
        
        base_name = self.i_name if type == 'img' else self.m_name
        name = f'{base_name}_{rl.scene.name}_{rl.layer}_{npass.name}'
        return name
        
    def add_passes_mix_imgs(self):
        '''
        Add image and mix nodes for each individual pass of each active
        Render layers node in the main scene Compositor
        '''
        
        _links = self.project['main_sc'].node_tree.links
        y_loc = 0
        for lnk in self.links:
            y_loc += 1
            nodes = self.add_mix_img()
            m_node = self.set_mix_node(nodes[1], lnk.node, lnk, y_loc)                
            i_name = self.get_name('img', lnk.node, lnk)
            i_image = self.set_image(i_name)
            i_node = self.set_img_node(nodes[0], i_image, m_node)
            i_node.label = m_node.label = lnk.name
            _links.new(lnk, m_node.inputs[1])
            _links.new(i_node.outputs[0], m_node.inputs[2])
            _passes = self.rlayers[lnk.node.scene]['rlayers'][lnk.node]
            _passes[lnk]['image'] = i_image
            _passes[lnk]['img_node'] = i_node
            _passes[lnk]['mix_node'] = m_node
            self.restore['mix_nodes'].append(m_node)
            self.render['images'].append(i_image)
                
    def execute(self, context):
        self.structure()
        self.remove_existing()
        self.add_passes_mix_imgs()
        return {'FINISHED'}
    
#-------------------------------- Scenes Setup ---------------------------------     
               
class TMB_ScenesSetup(bpy.types.Operator):
    '''Setup all Eevee scenes with TMB enabled before render'''
    bl_idname = "tmb.scsetup"
    bl_label = "Scenes Setup"
    store = None
    project = None
    scenes = None
    scene = None
    
    def structure(self):
        '''Sync to the main storage'''
        
        self.store = bpy.types.TMB_OT_store.store
        self.project = self.store['Project']
        self.scenes = self.store['Scenes']
        self.scene = self.project['main_sc']
    
    def getsamples(self, scene):
        '''Calculate Eevee render samples based on the TMB settings'''
        
        sc = self.scenes[scene]
        tmb = sc['tmb']
        sc_samples = sc['samples']
        samples = tmb['samples']
        boost = tmb['boost']
        basic_samples = max(
            1, int(
                sc_samples // max(1, samples)
            )
        )
        samples = basic_samples + int(
            (sc_samples-basic_samples) * min(1, boost)
            )
        samples = min(samples, sc_samples)
        return samples
    
    def scsetup(self, sc):
        '''Set render samples number for all Eevee scenes with TMB enabled'''
        
        _sets = self.scenes[sc]
        _tmb = _sets['tmb']
        if _sets['engine'] == 'BLENDER_EEVEE' and _tmb and _tmb['activate']:
            sc.eevee.taa_render_samples = self.getsamples(sc)
            sc.eevee.use_motion_blur = False
    
    def execute(self, context):
        self.structure()
        for sc in list(self.scenes.keys()):
            self.scsetup(sc)
        return {'FINISHED'}
    
#----------------------- Enable Backdrop in Compositor -------------------------        
            
class TMB_Backdrop(bpy.types.Operator):
    '''Enable Show Backdrop in Compositor'''
    bl_idname = "tmb.backdrop"
    bl_label = "Enable Backdrop"
    store = None
    project = None
    restore = None
    override = None
    
    def structure(self):
        '''sync to the main storage'''
        
        self.store = bpy.types.TMB_OT_store.store
        self.project = self.store['Project']
        self.restore = self.store['Restore']
    
    def context_override(self):
        window = self.project['window']
        screen = window.screen
        area = None
        for ar in window.screen.areas:
            if ar.ui_type not in ('PROPERTIES','OUTLINER'):
                area = ar
        if not area:
            area = window.screen.areas[0]
        region = area.regions[0]
        scene = bpy.context.scene

        self.override = {'window':window,
                    'screen':screen,
                    'area'  :area,
                    'region':region,
                    'scene' :scene,
                    }
    
    def execute(self, context):
        self.store = bpy.types.TMB_OT_store.store
        self.project = self.store['Project']
        self.restore = self.store['Restore']
        _areas = self.project['window'].screen.areas        
        for area in _areas:
            if area.ui_type == 'CompositorNodeTree':
                area.spaces[0].show_backdrop = True
                return {'FINISHED'}
        self.context_override()
        override = self.override
        bpy.ops.screen.area_split(override, direction='VERTICAL', factor = .3)
        _areas[-1].ui_type = 'CompositorNodeTree'
        _areas[-1].spaces[0].show_backdrop = True
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return self.execute(context)
    
############################# EXECUTE SETUP OPERATOR ###########################

class TMB_Setup(bpy.types.Operator):
    '''Setup project for TMB render'''
    bl_idname = "tmb.setup"
    bl_label = "Setup"
    animation : BoolProperty(
        name="Animation",
        description="Render Animation",
        default=False,
        )
    project = None
    
    def execute(self, context):
        sc = context.scene
        _tmb = sc.true_mb
        bpy.ops.tmb.store(animation = self.animation)
        self.project = bpy.types.TMB_OT_store.store['Project']
        bpy.ops.tmb.rlayers()
        if not [
            rl for rl in self.project['rlayers']
            if rl.scene.view_layers[rl.layer].use
        ]:
            return {'CANCELLED'}
        bpy.ops.tmb.userouts()
        bpy.ops.tmb.links()
        bpy.ops.tmb.savebuffers()
        bpy.ops.tmb.miximgs()
        bpy.ops.tmb.scsetup()
        bpy.ops.tmb.backdrop('INVOKE_DEFAULT')
        return {'FINISHED'}
    
############################### RESTORE OPERATOR ###############################

class TMB_Restore(TMB_Helpers, bpy.types.Operator):
    '''Restore settings'''
    bl_idname = "tmb.restore"
    bl_label = 'Restore'
    store = None
    project = None
    scenes = None
    restore = None
    scene = None
    
    def structure(self):
        '''Sync to the main storage'''
        
        self.store = bpy.types.TMB_OT_store.store
        self.project = self.store['Project']
        self.scenes = self.store['Scenes']
        self.restore = self.store['Restore']
        self.scene = self.project['main_sc']
        
    def restore_settings(self, context):
        '''Retore initial render settings for Eevee TMB scenes'''
        
        self.project['main_sc'].frame_set(self.project['frame'], subframe=0.0)
        for sc in list(self.scenes.keys()):
            _sets = self.scenes[sc]
            _tmb = _sets['tmb'] 
            if _sets['engine'] == 'BLENDER_EEVEE' and _tmb and _tmb['activate']:
                sc.eevee.taa_render_samples = _sets['samples']
                sc.eevee.use_motion_blur = _sets['mb']
        self.project['main_sc'].render.filepath = self.project['user_path']
            
    def restore_viewer(self, sets):
        '''Recreate deleted Viewer'''
        
        sc = self.scene
        links = self.scene.node_tree.links
        viewer = sc.node_tree.nodes.new('CompositorNodeViewer')
        viewer.name = sets['name']
        viewer.label = sets['label']
        viewer.color = sets['color']
        viewer.height = sets['height']
        viewer.hide = sets['hide']
        viewer.location = sets['location']
        viewer.center_x = sets['center_x']
        viewer.center_y = sets['center_y']
        viewer.mute = False
        viewer.show_options = sets['show_options']
        viewer.show_preview = sets['show_preview']
        viewer.show_texture = sets['show_texture']
        viewer.use_alpha = sets['use_alpha']
        viewer.use_custom_color = sets['use_custom_color']
        viewer.width = sets['width']
        viewer.width_hidden = sets['width_hidden']
        _viewer_inputs = [inp.name for inp in viewer.inputs]
        for i in list(sets['inputs'].keys()):
            input = sets['inputs'][i]
            if input['name'] in _viewer_inputs:
                inp = viewer.inputs[input['name']]
            else:
                inp = viewer.inputs.new(
                    input['type'], input['name'], input['identifier']
                )
            inp.hide = input['hide']
            inp.enabled = input['enabled']
        for node in sc.node_tree.nodes:
            if node.type == 'COMPOSITE' and node.inputs[0].links:                
                links.new(
                    node.inputs[0].links[0].from_socket,
                    viewer.inputs[0])
                viewer.location = node.location
                viewer.location.y -= 150
                break
    
    def restore_compositor(self):
        '''
        Set all TMB Mix (Alpha Over) nodes mix factor to 1
        Unmute temporary muted nodes
        Remove temporary TMB supporting nodes
            except TMB Render Layers and Composite nodes
        Recreate and relink the Viewer        
        '''
        
        sc = self.scene
        if not sc.node_tree or not sc.node_tree.links:
            return
        links = sc.node_tree.links
        if self.restore['mix_nodes']:
            for node in self.restore['mix_nodes']:
                node.inputs[0].default_value = 1
        if self.restore['muted']:
            for node in self.restore['muted']:
                node.mute = False
        if self.restore['tmb_nodes']:
            for node in self.restore['tmb_nodes']:
                if node.type not in ('R_LAYERS', 'COMPOSITE'):
                    sc.node_tree.nodes.remove(node)
                elif node.type == 'COMPOSITE':
                    comps = [
                        nd for nd in sc.node_tree.nodes
                        if nd.type == 'COMPOSITE'
                    ]
                    if len(comps) > 1:
                        for nd in sc.node_tree.nodes:
                            if nd.type == 'COMPOSITE' and nd is not node:
                                if node.inputs[0].links:
                                    links.new(
                                        node.inputs[0].links[0].from_socket,
                                        nd.inputs[0]
                                    )
                                    sc.node_tree.nodes.remove(node)
                                    break
        if self.restore['viewers']:
            for viewer in list(self.restore['viewers'].keys()):
                self.restore_viewer(self.restore['viewers'][viewer])
        for rl in self.project['rlayers']:
            rl.mute = False
        
    def remove_out_dir(self):
        '''Remove temporary main out folder from disc'''
        
        _dest = self.project['path']
        _source = pathlib.os.path.join(_dest, 'TMB_Output')
        _spath = pathlib.Path(_source)
        if not _spath.is_dir():
            return
        _spath.rmdir()
    
    def cleanup(self):
        '''Remove temporary subframes folders from disc'''
        
        if (
            self.restore['main_dir'] and
            pathlib.os.path.isdir(self.restore["main_dir"])
        ):
            self.clear_path(self.restore["main_dir"])
    
    def execute(self, context):
        self.structure()
        self.restore_settings(context)
        self.restore_compositor()
        self.remove_out_dir()
        self.cleanup()
        return {'FINISHED'}
    
#--------------------------- For test purposes only ----------------------------

classes = [
    TMB_Warning,
    TMB_Store,
    TMB_RLayers,
    TMB_Links,
    TMB_SaveBuffers,
    TMB_AddMixImages,
    TMB_UserOutputs,
    TMB_ScenesSetup,
    TMB_Backdrop,
    TMB_Setup,
    TMB_Restore,
    ]    
    
def support_register():
    for cl in classes:
        register_class(cl)

def support_unregister():
    for cl in classes:
        unregister_class(cl)

if __name__ == '__main__':
    support_register()
    bpy.ops.tmb.setup()
    bpy.ops.tmb.restore()