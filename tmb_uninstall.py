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
#  TMB uninstall operators
#  (c) 2020 Andrey Sokolov (so_records)

import bpy

#------------------------- Bring back native Top Menu --------------------------

class TOPBAR_MT_render(bpy.types.Menu):
    bl_label = "Render"

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render

        layout.operator("render.render", text="Render Image",
                        icon='RENDER_STILL').use_viewport = True
        props = layout.operator(
            "render.render", text="Render Animation", icon='RENDER_ANIMATION')
        props.animation = True
        props.use_viewport = True

        layout.separator()

        layout.operator("sound.mixdown", text="Render Audio...")

        layout.separator()

        layout.operator("render.view_show", text="View Render")
        layout.operator("render.play_rendered_anim", text="View Animation")

        layout.separator()

        layout.prop(rd, "use_lock_interface", text="Lock Interface")

#------------------------------ Restore shortcuts ------------------------------

class TMB_KeyconfigRestore(bpy.types.Operator):
    bl_idname = 'tmb.keyconfig_restore'
    bl_label = 'Keyconfig'

    def execute(self, context):
        try:
            bpy.ops.tmb.keyconfig()
        except:
            pass
        configs = context.window_manager.keyconfigs
        items = configs.active.keymaps['Screen'].keymap_items
        keymap = [i for i in items if i.idname == "tmb_render.render"]
        for i in keymap:
            i.idname = "render.render"
            i.properties.use_viewport = True
        keymap[1].properties.animation = True
        return {'FINISHED'}