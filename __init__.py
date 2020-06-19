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
#  Initializing script
#  (c) 2020 Andrey Sokolov (so_records)

bl_info = {
    "name": "True Motion Blur",
    "author": "Andrey Sokolov",
    "version": (1, 0, 0),
    "blender": (2, 83, 0),
    "location": "Render Settings > True Motion Blur",
    "description": "True subframe motion blur for Eevee",
    "warning": "Creates and deletes temporary folders and files in render directory",
    "wiki_url": "https://github.com/sorecords",
    "tracker_url": "https://instagram.com/so_records/",
    "category": "Render"
}

#------------------------------- Import Modules -------------------------------- 
import bpy
from bpy.props import PointerProperty
from bpy.utils import register_class, unregister_class
from .tmb_ui import *
from .tmb_render import *
from .tmb_support import *

#--------------------------- Operators to register ----------------------------- 
classes = [
        TMB_TrueMB,
        TMB_Keyconfig,
        TMB_PT_true_mb_panel,
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
        TMB_UpdatePreview,
        TMB_RenderVariables,
        TMB_RenderHelpers,
        TMB_Render,
        TMB_Restore,
        TOPBAR_MT_render,
    ]
    
#---------------------------------- Register -----------------------------------
def register():
    for cl in classes:
        register_class(cl)
    bpy.types.Scene.true_mb = PointerProperty(type=TMB_TrueMB)
    bpy.app.handlers.persistent(keyconfig)
    bpy.app.handlers.load_pre.append(keyconfig)

def unregister():
    op = bpy.types.TMB_OT_store
    op.enable = False
    from true_motion_blur.tmb_uninstall import TMB_KeyconfigRestore
    register_class(TMB_KeyconfigRestore)
    bpy.ops.tmb.keyconfig_restore()
    for i in reversed(classes):
        unregister_class(i)
    from true_motion_blur.tmb_uninstall import TOPBAR_MT_render
    register_class(TOPBAR_MT_render)
    unregister_class(TMB_KeyconfigRestore)
    
#--------------------------- For test purposes only ----------------------------
if __name__ == '__main__':
    register()