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
#  Add UI-items to Blender interface
#  (c) 2020 Andrey Sokolov (so_records)

#------------------------------- Import Modules --------------------------------

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    FloatProperty,
    StringProperty,
    PointerProperty #--------------------------- this one for test purposes only
    )
from bpy.utils import register_class, unregister_class

#------------------------------ Change Keyconfig -------------------------------

class TMB_Keyconfig(bpy.types.Operator):
    '''
    Redirect shortcuts for native Render Operator bpy.ops.render.render()
    (F12 and Ctrl+F12 by default)
    with TMB render operator bpy.ops.tmb_render.render()
    '''
    bl_idname = 'tmb.keyconfig'
    bl_label = 'Keyconfig'
    
    def execute(self, context):
        configs = context.window_manager.keyconfigs
        items = configs.active.keymaps['Screen'].keymap_items
        keymap = [i for i in items if i.idname == "render.render"]
        keymap_tmb = [i for i in items if i.idname == "render.render"]
        for i in keymap:
            i.idname = "tmb_render.render"
            i.properties.use_viewport = True
        if keymap_tmb:
            keymap_tmb[0].properties.animation = True
            keymap_tmb[0].properties.animation = False
        if keymap:
            keymap[1].properties.animation = True
        return {'FINISHED'}

#----------------------------- Activate Keyconfig ------------------------------

def keyconfig(self, context):
    '''
    Activate Keyconfig Operator
    Function to be loaded from Blender on_load handler
    It is necessary because Blender Operators can not be invoked on startup
    ''' 
       
    op = bpy.types.TMB_OT_store
    if not op.enable:
        op.enable = True
        bpy.ops.tmb.keyconfig()
    _on_load = bpy.app.handlers.load_pre
    if keyconfig in _on_load:
        _on_load.remove(keyconfig)

#----------------------------- Set TMB Properties ------------------------------

class TMB_TrueMB(bpy.types.PropertyGroup):
    '''Properties Group for UI Panel'''
    
    activate : BoolProperty(
        name="",
        description="Enable true subframe motion blur effect\
 (render only)",
        default=False,
        update=keyconfig
    )
    position : EnumProperty(
        name = "Position",
        description = "Offset for the shutter's time interval,\
 allows to change motion blur trails:",
        items = [
            ("START", "Start of Frame",
                "The shutter opens on the current frame."),
            ("CENTER", "Center of Frame",
                "The shutter is open during the current frame."),
            ("FRAME", "End of Frame",
                "The shutter closes on the current frame."),              
        ],
        default="CENTER"
    )
    samples : IntProperty(
        name="Samples",
        description="Number of subframes per frame",
        default=16,
        min=2,
        max=128
    )
    shutter : FloatProperty(
        name="Shutter",
        description="Time taken in frames between shutter open and close",
        default=.5,
        min=0,
        soft_max=1,
        subtype = "FACTOR"
    )
    boost : FloatProperty(
        name="Quality boost",
        description="Boost render samples for each subframe from normal amount\
 to original sample rate.\nRender time increases proportionally",
        default=0,
        min=0,
        max=1,
        subtype = "FACTOR"
    )
    render_passes : BoolProperty(
        name="Render Passes",
        description="Render all enabled render passes, even if they are \
not linked to any output",
        default=False,
        options={'HIDDEN'}
    )

#-------------------- Create UI Panel in Render Properties ---------------------
class TMB_Panel:
    '''Not an Operator class, doesn't need to be registered as Operator'''
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}
    bl_context = "render"
    bl_category = 'True Motion Blur add-on'
    COMPAT_ENGINES = {'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
    
    @classmethod
    def poll(cls, context):
        return (context.engine in cls.COMPAT_ENGINES)

class TMB_PT_true_mb_panel(TMB_Panel, bpy.types.Panel):
    '''Create UI Panel in the render properties window'''
    bl_label = "True Motion Blur"
    bl_idname = "RENDER_PT_true_mb"
    
    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.true_mb
        
        col = layout.column()
        col.prop(props, "activate")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        scene = context.scene
        props = scene.true_mb
        layout.active = props.activate
        col = layout.column()
        col.prop(props, "position")
        col.prop(props, "shutter")
        col.separator()        
        col.prop(props, "samples")
        col.prop(props, "boost")
        col.prop(props, "render_passes")

#-------------------------- Replace native Top Menu ----------------------------

#  This is almost exact copy of original Blender Render tab from top menu:
#  'render.render()' operator is replaced with 'tmb_render.render()'.
#  Note: in your scripts use `bpy.ops.render.render()` for native render
#  and `bpy.ops.tmb_render.render()` for True Motion Blur render.

class TOPBAR_MT_render(bpy.types.Menu):
    
    bl_label = "Render"
    bl_category = 'Render'

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render

        props = layout.operator("tmb_render.render", text="Render Image",
                        icon='RENDER_STILL')
        props.animation = False             
        props.use_viewport = True
        props = layout.operator("tmb_render.render",
                text="Render Animation", icon='RENDER_ANIMATION')
        props.animation = True
        props.use_viewport = True

        layout.separator()

        layout.operator("sound.mixdown", text="Render Audio...")

        layout.separator()

        layout.operator("render.view_show", text="View Render")
        layout.operator("render.play_rendered_anim", text="View Animation")

        layout.separator()

        layout.prop(rd, "use_lock_interface", text="Lock Interface")

#--------------------------- For test purposes only ----------------------------

classes = [
    TMB_TrueMB,
    TMB_PT_true_mb_panel,
    ]    

def ui_register():
    for cl in classes:
        register_class(cl)

def ui_unregister():
    for cl in classes:
        unregister_class(cl)
   
if __name__ == '__main__':
    ui_register()
    bpy.types.Scene.true_mb = PointerProperty(type=TMB_TrueMB)