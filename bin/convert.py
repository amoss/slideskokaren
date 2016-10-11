#!/usr/bin/env python
import argparse, sys, os, os.path, subprocess
from docutils.parsers.rst import Parser, roles
from docutils.frontend import OptionParser
import docutils.utils
from slides import Slide

def shell_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
  assert role=="shell"
  print text
  return [docutils.nodes.literal(text, docutils.nodes.Text(text), style="shell")], []
roles.register_local_role("shell",shell_role)

# Settings spec is non-trivial, don't export hooks into an argparser but use
# the structure to get the default values for parameters in the document.
# e.g. tab-width etc.
def parseRst(filename):
  '''Load a text file and use the .rst parser to build a docutils node tree.'''
  settings = OptionParser(components=(Parser,)).get_default_values()
  source = open(filename).read()
  parser = Parser()
  doc = docutils.utils.new_document('slides.rst',settings)
  parser.parse(source,doc)
  return doc


parser = argparse.ArgumentParser()
parser.add_argument('-f', '--folder',     type=str)
parser.add_argument('-i', '--input',      type=str)
parser.add_argument('-o', '--output',     type=str)
parser.add_argument('-s', '--forcestyle', action='store_true', default=False)
parser.add_argument('-j', '--forcejs',    action='store_true', default=False)
args = parser.parse_args()

if (args.input is None  or  args.output is None)  and args.folder is None:
  print "Either specify presentation folder or explicit filenames."
  print "Input defaults to folder/slides.rst"
  print "Output defaults to folder/index.html"
  sys.exit(-1)

if args.input is None:
  args.input = os.path.join(args.folder, "slides.rst")

if args.output is None:
  args.output = os.path.join(args.folder, "index.html")

doc = parseRst(args.input)
print "%d nodes under root" % len(doc.children)
presentation = []
counter = 1

def processDocTitle(node):
  for c in node.children:
    if   isinstance(c, docutils.nodes.title):
      titles['Name'] = str(c.children[0])     # Assume a single Text node.
    elif isinstance(c, docutils.nodes.field_list):
      for f in c.children:
        assert isinstance(f.children[0], docutils.nodes.field_name)  and  \
               isinstance(f.children[1], docutils.nodes.field_body)
        name = "".join([ str(x) for x in f.children[0].children ])
        titles[ name ] = Slide.renderText(f.children[1].children[0])
        
    elif isinstance(c, docutils.nodes.section):
      processSlide(c)
    else:
      print "Unexpected %s under document title:" % type(c)
      print c

def processSlide(slide):
  global counter
  if not isinstance(slide, docutils.nodes.section):
    print "Unexpected node under root:", type(slide), slide
    return
  if not isinstance(slide.children[0], docutils.nodes.title):
    print "No title node under section node?!"
    print slide.children
    return
  titleNode = slide.children[0]
  if not isinstance(titleNode.children[0], docutils.nodes.Text):
    print "No text in the title node!"
    return
  title = titleNode.children[0]

  # Check for a hashtag template name.
  template = 'Single'
  for t in Slide.templates:
    hashT = '#' + t
    if hashT in title:
      title = title.replace(hashT,'')
      template = t

  current = Slide(title='%d. %s'%(counter,title), template=template)
  counter += 1

  for node in slide.children[1:]:
    if isinstance(node, docutils.nodes.bullet_list)  or \
       isinstance(node, docutils.nodes.enumerated_list) :
      for subnode in node.children:
        if isinstance(subnode, docutils.nodes.list_item):
          current.addText(subnode,parent=node)

    elif isinstance(node, docutils.nodes.paragraph):
      current.addText(node)

    elif isinstance(node, docutils.nodes.image):
      path = os.path.join(args.folder, node.get('uri'))
      width, height = subprocess.Popen(['identify', '-format', '%w %h', path],
                                       stdout=subprocess.PIPE).communicate()[0].split(' ')
      current.addImage(node, aratio=float(width)/float(height))

    elif isinstance(node, docutils.nodes.topic):
      if isinstance(node.children[0], docutils.nodes.title)  and len(node.children)==2:
        current.addText(node)
      else:
        print "Unrecognised topic structure", node, node.children

    elif isinstance(node, docutils.nodes.literal_block):
      current.addText(node, parent=node)

    elif isinstance(node, docutils.nodes.block_quote):
      current.addText(node, parent=node)

    elif isinstance(node, docutils.nodes.table):
      current.addText(node, parent=node)

    else:
      print "Other!", node

  presentation.append(current)



titles = {}
# Using a document title changes the shape of the tree.
if len(doc.children)==1 and isinstance(doc.children[0],docutils.nodes.section):
  processDocTitle(doc.children[0])
else:
  for c in doc.children:
    processSlide(c)



with open(args.output, 'wt') as out:
  print >>out, '<html><head><title>%s</title>' % 'INSERT TITLE'
  print >>out, '<script src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML" type="text/javascript"></script>'
  print >>out, '<link href="styles.css" type="text/css" rel="stylesheet"></link>'
  print >>out, '</head><body>'
  print >>out, '''<script type="text/javascript">
  <script type="text/javascript">
   MathJax.Hub.Config({
     extensions:["mml2jax.js"],
     jax:["input/MathML","output/HTML-CSS"],
     "HTML-CSS": {
       styles: {
         '.MathJax_Display': {
            "margin": 0
          }
       }
     }
  });
  </script>'''
  print >>out, '<div id="slides">'
  print >>out, '<div class="S">'
  print >>out, '  <div class="Slogo"><img src="logo.svg"/></div>'
  if 'CourseCode' in titles:
    print >>out, '  <h1 style="margin:0; margin-top:0.5em">%s</h1>' % titles['CourseCode']
  if 'CourseName' in titles:
    print >>out, '  <h1 style="margin:0; margin-top:0.5em">%s</h1>' % titles['CourseName']
  if 'Date' in titles:
    print >>out, '  <p>%s</p>' % titles['Date']
  if 'Name' in titles:
    print >>out, '  <p>%s</p>' % titles['Name']
  print >>out, '</div>'
  print titles
  for s in presentation:
    s.render(out)
  print >>out, '</div>'
  print >>out, '</body></html>'

style = open('support/logo.svg', 'rt')
tar   = os.path.join(args.folder, 'logo.svg')
open(tar,'wt').write(style.read())

if args.forcestyle:
  style = open('support/styles.css', 'rt')
  tar   = os.path.join(args.folder, 'styles.css')
  open(tar,'wt').write(style.read())


if args.forcejs:
  js = open('support/slides.js', 'rt')
  tar   = os.path.join(args.folder, 'slides.js')
  open(tar,'wt').write(js.read())
