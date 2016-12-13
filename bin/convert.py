#!/usr/bin/env python
import argparse, sys, os, os.path, subprocess, shutil
from StringIO import StringIO
from docutils.parsers.rst import Parser, roles
from docutils.frontend import OptionParser
from docutils.parsers.rst import Directive, directives
from docutils import nodes
import docutils.utils
import slides
from slides import Slide, TableVisitor

class Video(Directive):
  required_arguments = 1
  def run(self):
    tag='<video width="100%%" style="max-width:100%%; max-height:95%%" controls><source src="%s.webm" type="video/webm;"><source src="%s.mov" type="video/quicktime;"></video>' % (self.arguments[0], self.arguments[0])
    return [nodes.raw(rawtext=tag, slidepos='video', format='html')]
directives.register_directive('video', Video)

class Reference(Directive):
  required_arguments = 0
  option_spec = { 'title' : str,  'author' : str, 'url' : str }
  def run(self):
    rows = []
    if 'title' in self.options:
      rows.append( '<td>"%s"</td>' % self.options['title'] )
    if 'author' in self.options:
      rows.append( '<td><i>%s</i><td>' % self.options['author'] )
    if 'url' in self.options:
      rows.append( '<td><a href="%s">%s</a></td>' % (self.options['url'], self.options['url']) )

    tag='<div class=bibitem><table style="width=100%%"><tr><td rowspan="%d"><img src="book-icon.png"/>%s</td></tr>%s</table></div>' % (len(rows), rows[0], "".join(['<tr>%s</tr>'%r for r in rows[1:]]))
    return [nodes.raw(rawtext=tag, slidepos="text", format='html')]
directives.register_directive('reference', Reference)

class Shell(Directive):
  required_arguments = 0
  has_content = True
  def run(self):
    rows = [self.content[i] for i in range(len(self.content)) ]
    print repr(rows)
    tag='<div class=shell>%s</div>' % "\n".join(rows)
    return [nodes.raw(rawtext=tag, slidepos="text", format='html')]
directives.register_directive('shell', Shell)

def shell_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
  assert role=="shell"
  return [docutils.nodes.literal(text, docutils.nodes.Text(text), style="shell")], []
roles.register_local_role("shell",shell_role)

# Settings spec is non-trivial, don't export hooks into an argparser but use
# the structure to get the default values for parameters in the document.
# e.g. tab-width etc.
def parseRst(filename):
  '''Load a text file and use the .rst parser to build a docutils node tree.'''
  settings = OptionParser(components=(Parser,)).get_default_values()
  settings.input_encoding = 'utf8'    # This does not work, old version of docutils?
  source = open(filename).read()
  parser = Parser()
  doc = docutils.utils.new_document('slides.rst',settings)
  parser.parse(source,doc)
  return doc


parser = argparse.ArgumentParser()
parser.add_argument('source',              type=str)
parser.add_argument('outputFolder',        type=str)
parser.add_argument('-d', '--debug',       action='store_true', default=False)
parser.add_argument('-i', '--inputFolder', type=str)
args = parser.parse_args()
slides.debugFlag = args.debug
if args.inputFolder is None:  args.inputFolder = args.outputFolder

doc = parseRst(args.source)
print "%d nodes under root" % len(doc.children)
presentation = []
counter = 1
toc = None

def processDocTitle(node):
  global toc
  for c in node.children:
    if   isinstance(c, docutils.nodes.title):
      titles['Name'] = str(c.children[0])     # Assume a single Text node.
    elif isinstance(c, docutils.nodes.field_list):
      for f in c.children:
        assert isinstance(f.children[0], docutils.nodes.field_name)  and  \
               isinstance(f.children[1], docutils.nodes.field_body)
        name = "".join([ str(x) for x in f.children[0].children ])
        titles[ name ] = Slide.renderText(f.children[1].children[0])
        
    elif isinstance(c, docutils.nodes.table):
      toc = c
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

  if args.debug:
    print "Slide.children"
    print "\n".join([ '  '+str(x) for x in slide.children ])

  for node in slide.children[1:]:
    if isinstance(node, docutils.nodes.bullet_list)  or \
       isinstance(node, docutils.nodes.enumerated_list) :
      for subnode in node.children:
        if isinstance(subnode, docutils.nodes.list_item):
          current.addText(subnode,parent=node)

    elif isinstance(node, docutils.nodes.definition_list):
      for subnode in node.children:
        current.addText(subnode,parent=node)

    elif isinstance(node, docutils.nodes.paragraph):
      current.addText(node)

    elif isinstance(node, docutils.nodes.image):
      #path = os.path.join(args.inputFolder, node.get('uri'))
      # Temporarily removed the image-magick calls so it is not a dependency at
      # install time as we do not currently use the aspect ratio for layout.
      #width, height = subprocess.Popen(['identify', '-format', '%w %h', path],
      #                                 stdout=subprocess.PIPE).communicate()[0].split(' ')
      #current.addImage(node, aratio=float(width)/float(height))
      current.addImage(node, aratio=1.0)

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

    elif isinstance(node, docutils.nodes.raw):
      if node['slidepos'] == 'video':
        current.addRaw(node['rawtext'])
      elif node['slidepos'] == 'text':
        current.addText(node, parent=None)
      else:
        assert False, "Unknown slidepos in raw node! %s" % node['slidepos']

    else:
      print "Other!", node

  presentation.append(current)

def wrapSlides(path, aspect):
  with open(path, 'wt') as out:
    print >>out, '<html><head><title>%s</title>' % titles['Name']
    print >>out, '<script src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML" type="text/javascript"></script>'
    print >>out, '<link href="styles.css" type="text/css" rel="stylesheet"></link>'
    print >>out, '''\
  <script src="slides.js" type="text/javascript">
  var query = window.location.search.substring(1);
  var vars = query.split("&");
  console.log(vars)
  </script>'''
    print >>out, '</head><body>'
    print >>out, '''\
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
    print >>out, '<div id="navpanel"><a><img src="leftarrow.svg" class="icon" onclick="javascript:leftButton()" id="navleft"></img></a><a><img src="rightarrow.svg" class="icon" onclick="javascript:rightButton()" id="navright"></img></a><a><img src="closearrow.svg" class="icon" onclick="javascript:navcloseButton()" id="navclose"></img></a></div>'
    print >>out, '<div id="slides">'
    print >>out, '<div class="S%s">' % aspect
    print >>out, '  <div class="Slogo"><img src="logo.svg"/></div>'
    if 'CourseCode' in titles:
      print >>out, '  <h1 style="margin:0; margin-top:0.5em">%s</h1>' % titles['CourseCode']
    if 'CourseName' in titles:
      print >>out, '  <h1 style="margin:0; margin-top:0.5em">%s</h1>' % titles['CourseName']
    if 'Date' in titles:
      print >>out, '  <p>%s</p>' % titles['Date']
    if 'Name' in titles:
      print >>out, '  <p><i>%s</i></p>' % titles['Name']
    if toc is not None:
      print "Doing the TOC"
      filelike = StringIO()
      TableVisitor(toc).visit(filelike)
      print >>out, filelike.getvalue()
    print >>out, '</div>'
    for s in presentation:
      s.render(out, aspect)
    print >>out, '</div>'
    print >>out, '</body></html>'


titles = {}
# Using a document title changes the shape of the tree.
if len(doc.children)==1 and isinstance(doc.children[0],docutils.nodes.section):
  processDocTitle(doc.children[0])
else:
  for c in doc.children:
    processSlide(c)

##### Start building the output ##############

if not os.path.isdir(args.outputFolder):
  os.makedirs(args.outputFolder)

manifest = []
for idxAspect in ('43', '169'):
  fn = "index-%s.html"%idxAspect
  wrapSlides(os.path.join(args.outputFolder,fn), idxAspect)
  manifest.append(fn)

for fn in os.listdir('support'):
  shutil.copyfile( os.path.join('support',fn), os.path.join(args.outputFolder,fn))
  manifest.append(fn)
if args.inputFolder != args.outputFolder:
  for fn in os.listdir(args.inputFolder):
    shutil.copyfile( os.path.join(args.inputFolder,fn), os.path.join(args.outputFolder,fn))
    manifest.append(fn)

with open( os.path.join(args.outputFolder, 'manifest.py'), 'wt' ) as out:
  print >>out, '''\
from twisted.web.resource import Resource
from twisted.web.static   import File
def build():
  self = Resource()'''
  for x in manifest:
    print >>out, '  self.putChild("%s", File("%s"))' % (x, os.path.join(args.outputFolder,x) )
  print >>out, '  return self'

with open( os.path.join(args.outputFolder, '__init__.py'), 'wt') as out:
  print >>out, '# Nothing here'
