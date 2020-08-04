import declxml
from xml.etree import cElementTree as ElementTree

tree = ElementTree.parse('icsConfig.xml')
root = tree.getroot()