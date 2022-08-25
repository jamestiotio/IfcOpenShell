
# IfcSverchok - IFC Sverchok extension
# Copyright (C) 2020, 2021 Dion Moult <dion@thinkmoult.com>
#
# This file is part of IfcSverchok.
#
# IfcSverchok is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IfcSverchok is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IfcSverchok.  If not, see <http://www.gnu.org/licenses/>.

import bpy
import ifcopenshell
import ifcopenshell.api
import ifcsverchok.helper
from bpy.props import StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode





class SvIfcTooltip(bpy.types.Operator):
    bl_idname = "node.sv_ifc_tooltip"
    bl_label = "IFC Info"
    tooltip: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        return {"FINISHED"}


class SvIfcApi(bpy.types.Node, SverchCustomTreeNode, ifcsverchok.helper.SvIfcCore):

    def update_usecase(self, context):
        try:
            module_usecase = self.get_module_usecase()
            if module_usecase:
                self.generate_node(*module_usecase)
        except:
            raise Exception(
                f"Couldn't run generate_node(). Module usecase: {module_usecase}"
            )

    bl_idname = "SvIfcApi"
    bl_label = "IFC API"
    tooltip: StringProperty(name="Tooltip")
    usecase: StringProperty(update=updateNode)

    def sv_init(self, context):
        input_socket = self.inputs.new("SvStringsSocket", "usecase").use_prop = True
        input_socket.tooltip = "ifcopenshell.api usecase, written like 'module.usecase' \n E.g.: 'project.create_file'"
        self.outputs.new("SvVerticesSocket", "file")

    def draw_buttons(self, context, layout):
        op = layout.operator("node.sv_ifc_tooltip", text="", icon="QUESTION", emboss=False)
        op.tooltip = self.tooltip

    def process(self):
        print("process")
        module_usecase = self.get_module_usecase()
        if module_usecase:
            self.generate_node(*module_usecase)
            self.sv_input_names = [i.name for i in self.inputs]
            super().process() # super().process() uses zip_long_repeat() which doesn't take objects like bmesh

    def get_module_usecase(self):
        usecase = self.inputs["usecase"].sv_get()[0][0]
        if usecase:
            return usecase.split(".")

    def generate_node(self, module, usecase):
        try:
            node_data = ifcopenshell.api.extract_docs(module, usecase)
        except:
            raise Exception("Node not yet implemented:", module, usecase)
            return
        while len(self.inputs) > 1:
            self.inputs.remove(self.inputs[-1])

        self.tooltip = ""
        for name, data in node_data["inputs"].items():
            setattr(SvIfcApi, name, StringProperty(name=name, update=updateNode))
            self.inputs.new("SvStringsSocket", name).use_prop = True
            if "default" in data:
                self.tooltip = f"{name} ({data['default']}): {data['description']}\n"
            else:
                self.tooltip = f"{name}: {data['description']}\n"
        self.tooltip = self.tooltip.strip()

    def process_ifc(self, usecase, *setting_values):
        if usecase:
            settings = dict(zip(self.sv_input_names[1:], setting_values))
            settings = {k: v for k, v in settings.items() if v != ""}
            self.outputs["file"].sv_set([ifcopenshell.api.run(usecase, **settings)])



def register():
    bpy.utils.register_class(SvIfcTooltip)
    bpy.utils.register_class(SvIfcApi)


def unregister():
    bpy.utils.unregister_class(SvIfcApi)
    bpy.utils.unregister_class(SvIfcTooltip)