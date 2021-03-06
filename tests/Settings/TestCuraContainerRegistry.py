# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os #To find the directory with test files and find the test files.
import pytest #This module contains unit tests.
import shutil #To copy files to make a temporary file.
import unittest.mock #To mock and monkeypatch stuff.
import urllib.parse

from cura.Settings.CuraContainerRegistry import CuraContainerRegistry #The class we're testing.
from cura.Settings.ExtruderStack import ExtruderStack #Testing for returning the correct types of stacks.
from cura.Settings.GlobalStack import GlobalStack #Testing for returning the correct types of stacks.
from UM.Resources import Resources #Mocking some functions of this.
import UM.Settings.ContainerRegistry #Making empty container stacks.
import UM.Settings.ContainerStack #Setting the container registry here properly.
from UM.Settings.DefinitionContainer import DefinitionContainer

##  Gives a fresh CuraContainerRegistry instance.
@pytest.fixture()
def container_registry():
    return CuraContainerRegistry()

def teardown():
    #If the temporary file for the legacy file rename test still exists, remove it.
    temporary_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stacks", "temporary.stack.cfg")
    if os.path.isfile(temporary_file):
        os.remove(temporary_file)

##  Tests whether loading gives objects of the correct type.
@pytest.mark.parametrize("filename,                  output_class", [
                        ("ExtruderLegacy.stack.cfg", ExtruderStack),
                        ("MachineLegacy.stack.cfg",  GlobalStack),
                        ("Left.extruder.cfg",        ExtruderStack),
                        ("Global.global.cfg",        GlobalStack),
                        ("Global.stack.cfg",         GlobalStack)
])
def test_loadTypes(filename, output_class, container_registry):
    #Mock some dependencies.
    UM.Settings.ContainerStack.setContainerRegistry(container_registry)
    Resources.getAllResourcesOfType = unittest.mock.MagicMock(return_value = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "stacks", filename)]) #Return just this tested file.

    def findContainers(container_type = 0, id = None):
        if id == "some_instance":
            return [UM.Settings.ContainerRegistry._EmptyInstanceContainer(id)]
        elif id == "some_definition":
            return [DefinitionContainer(container_id = id)]
        else:
            return []

    container_registry.findContainers = findContainers

    with unittest.mock.patch("cura.Settings.GlobalStack.GlobalStack.findContainer"):
        with unittest.mock.patch("os.remove"):
            container_registry.load()

    #Check whether the resulting type was correct.
    stack_id = filename.split(".")[0]
    for container in container_registry._containers: #Stupid ContainerRegistry class doesn't expose any way of getting at this except by prodding the privates.
        if container.getId() == stack_id: #This is the one we're testing.
            assert type(container) == output_class
            break
    else:
        assert False #Container stack with specified ID was not loaded.

##  Tests whether loading a legacy file moves the upgraded file properly.
def test_loadLegacyFileRenamed(container_registry):
    #Create a temporary file for the registry to load.
    stacks_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stacks")
    temp_file = os.path.join(stacks_folder, "temporary.stack.cfg")
    temp_file_source = os.path.join(stacks_folder, "MachineLegacy.stack.cfg")
    shutil.copyfile(temp_file_source, temp_file)

    #Mock some dependencies.
    UM.Settings.ContainerStack.setContainerRegistry(container_registry)
    Resources.getAllResourcesOfType = unittest.mock.MagicMock(return_value = [temp_file]) #Return a temporary file that we'll make for this test.

    def findContainers(container_type = 0, id = None):
        if id == "MachineLegacy":
            return None

        container = UM.Settings.ContainerRegistry._EmptyInstanceContainer(id)
        container.getNextStack = unittest.mock.MagicMock()
        return [container]

    old_find_containers = container_registry.findContainers
    container_registry.findContainers = findContainers

    with unittest.mock.patch("cura.Settings.GlobalStack.GlobalStack.findContainer"):
        container_registry.load()

    container_registry.findContainers = old_find_containers

    container_registry.saveAll()
    print("all containers in registry", container_registry._containers)
    assert not os.path.isfile(temp_file)
    mime_type = container_registry.getMimeTypeForContainer(GlobalStack)
    file_name = urllib.parse.quote_plus("MachineLegacy") + "." + mime_type.preferredSuffix
    path = Resources.getStoragePath(Resources.ContainerStacks, file_name)
    assert os.path.isfile(path)
