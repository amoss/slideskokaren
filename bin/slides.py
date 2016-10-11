import docutils.utils
import subprocess, cgi
from StringIO import StringIO


class Slide(object):
  templates = ("Cols", "Rows", "Single")

  def __init__(self, template="Single", title="empty"):
    assert template in self.templates
    self.template = template
    self.title    = title
    self.texts = []
    self.images  = []

  def addText(self, node, parent=None):
    if parent is None:
      self.texts.append( ("plain", node) )
    elif isinstance(parent, docutils.nodes.enumerated_list):
      self.texts.append( ("numbered", node) )
    elif isinstance(parent, docutils.nodes.bullet_list):
      self.texts.append( ("bulleted", node) )
    elif isinstance(node,   docutils.nodes.topic):
      self.texts.append( ("callout", node) )
    elif isinstance(node,   docutils.nodes.literal_block):
      self.texts.append( ("verbatim", node) )
    elif isinstance(node,   docutils.nodes.block_quote):
      self.texts.append( ("quote",   node) )
    elif isinstance(node,   docutils.nodes.table):
      self.texts.append( ("table",   node) )
    else:
      assert False, "Unrecognised text-parent: %s" % node

  def addImage(self, node, aratio=None):
    assert isinstance(node, docutils.nodes.image)
    self.images.append( (node.get('uri'), aratio) )

  def render(self, out):
    print >>out, '<div class="S">'
    print >>out, '  <div class="Stitle"><h1>%s</h1></div>' % self.title
    print >>out, '  <div class="Slogo"><img src="logo.svg"/></div>'
    print >>out, '  <div class="Sin">'
    getattr(self, 'render'+self.template)(out)
    print >>out, '  </div>'
    print >>out, '</div>'
    print >>out

  
  @staticmethod
  def renderText(node):
    '''The docutils tree must convert to a single paragraph text-only 
       representation (i.e. it must be equivalent to a list of spans,
       not include any block level structure) otherwise it is an error. 
       One (at most) enclosing paragraph node is stripped off.         '''
    if isinstance(node, docutils.nodes.paragraph):
      root = node.children
    else:
      root = [node]

    def conv(docNode):
      if isinstance(docNode, docutils.nodes.emphasis):
        return '<em>%s</em>' % docNode.children[0]
      if isinstance(docNode, docutils.nodes.strong):
        return '<b>%s</b>'   % docNode.children[0]
      if isinstance(docNode, docutils.nodes.literal):
        style = docNode.attributes.get("style", "program")
        print style, docNode.children
        return '<code class="%s">%s</code>' % (style, cgi.escape(docNode.children[0]))
      if isinstance(docNode, docutils.nodes.Text):
        return str(docNode)
      if isinstance(docNode, docutils.nodes.reference):
        return '<a href="%s">%s</a>' % (docNode.attributes['refuri'], docNode.attributes['name'])
      if isinstance(docNode, docutils.nodes.target):

        return ''
      assert False, "Can't span-convert (%s) %s" % (type(docNode), docNode)


    result = [ conv(x) for x in root ]
    return "".join(result)




  def renderTextsDiv(self, out):
    tagName = { 'bulleted':'ul', 'numbered':'ol' }  # No "plain" or "callout"
    inList = [None]             # Alias to force sharing with inner-proc

    def enter(kind):
      if inList[0] not in (None,kind):        
        print >>out, "</%s>"%tagName[inList[0]]
        inList[0] = None
      if inList[0]!=kind  and  kind in tagName.keys():  
        print >>out, "<%s>" % tagName[kind]
        inList[0] = kind

    for nkind, node in self.texts:
      enter(nkind)
      if   isinstance(node, docutils.nodes.list_item):
        print >>out, '<li>%s</li>' % Slide.renderText(node.children[0])
      elif isinstance(node, docutils.nodes.paragraph):
        print >>out, '<p>%s</p>'   % Slide.renderText(node.children[0])
      elif isinstance(node, docutils.nodes.topic):
        assert isinstance(node.children[0], docutils.nodes.title)
        print >>out, '<div class="Scallo"><div class="ScalloHd">%s</div>%s</div>' % \
                     (Slide.renderText(node.children[0].children[0]), 
                      Slide.renderText(node.children[1]))
      elif isinstance(node, docutils.nodes.literal_block):
        style = node.attributes['classes']
        if len(style)==0:  style = ['verbatim']
        style = style[0]
        print style
        print >>out, '<div class="%s">%s</div>' % (style, str(node.children[0]))

      elif isinstance(node, docutils.nodes.block_quote):
        print >>out, '<div class="quotebegin">&#8220;</div>'
        print >>out, '<div class="quoteinside">%s</div>' % str(node.children[0])
        if len(node.children)>1  and  isinstance(node.children[-1], docutils.nodes.attribution):
          print >>out, '- %s' % str(node.children[-1])
        print >>out, '<div class="quoteend">&#8221;</div>'

      elif isinstance(node, docutils.nodes.table):
        filelike = StringIO()
        TableVisitor(node).visit(filelike)
        print >>out, filelike.getvalue()

      else:
        assert False, "Don't know how to render %s" % node
    if inList[0] is not None:
      print >>out, '     </%s>' % tagName[inList[0]]



  def renderImagesDiv(self, out):
    '''Use aspect-ratio to determine constraints.'''
    for img in self.images:
      print img
      print >>out, '<img src="%s" style="width:100%%; height:100%%; object-fit:contain"/>' % img[0]


  def renderSingle(self, out):
    if   len(self.images)>0  and len(self.texts)==0:
      self.renderImagesDiv(out)
    elif len(self.texts)>0   and len(self.images)==0:
      self.renderTextsDiv(out)
    elif len(self.texts)==0  and len(self.images)==0:
      print "Blank"
    else:
      assert False, 'Slide template is single, but has both text and images'

  def renderCols(self, out):
    print >>out, '  <div style="width:49%; display:inline-block; vertical-align:top">'
    self.renderTextsDiv(out)
    print >>out, '  </div>'
    print >>out, '  <div style="width:49%; display:inline-block; margin-left:1%">'
    self.renderImagesDiv(out)
    print >>out, '  </div>'

  def renderRows(self, out):
    print >>out, '  <div style="width:100%; display:inline-block">'
    self.renderTextsDiv(out)
    print >>out, '  </div>'
    print >>out, '  <div style="width:100%; display:inline-block">'
    self.renderImagesDiv(out)
    print >>out, '  </div>'



class TableVisitor(object):

  def __init__(self,root):
    self.root=root
    self.inHeader=False

  def visit(self, fh, node=None):
    if node is None:  node=self.root
    fullName = str(node.__class__).split("'")[1]
    className = fullName.split('.')[-1]
    meth = getattr(self, 'visit_'+className, None)
    if meth is not None:
      meth(fh,node)
    #else:
    #  print "Skip Visit", className
    for c in node.children:
      self.visit(fh,c)
    meth = getattr(self, 'leave_'+className, None)
    if meth is not None:
      meth(fh, node)

  def visit_table(self, out, node):
    print >>out, '<table class="allborders">'

  def leave_table(self, out, node):
    print >>out, "</table>"

  def visit_row(self, out, node):
    print >>out, "<tr>"

  def leave_row(self, out, node):
    print >>out, "</tr>"

  def visit_entry(self, out, node):
    tag = 'th' if self.inHeader else 'td'
    attributes = ''
    if 'morecols' in node.attributes:
      attributes += ' colspan="%d"' % (int(node.attributes['morecols'])+1)
    if 'morerows' in node.attributes:
      attributes += ' rowspan="%d"' % (int(node.attributes['morerows'])+1)
    print >>out, "<%s%s>" % (tag,attributes)
    try:
      cell = Slide.renderText(node.children[0])
      print >>out, cell
    except:
      print >>out, "Missing block-level structure"

  def leave_entry(self, out, node):
    print >>out, "</td>"
    
  def visit_thead(self, out, node):
    self.inHeader = True
    
  def leave_thead(self, out, node):
    self.inHeader = False

