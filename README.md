# slideskokaren
Presentation Baker from RST to HTML.

Describe slides using a (very slightly) customized dialect of
RestructuredText. Convert them into a HTML/CSS/JS bundle for 
use on a web-server. The style baked into the presentations is
cloned from the course materials on http://mechani.se

## The example

For a quick demo `bin/convert.py -f example -j -s`. The source in 
the examples folder is augmented with slides.html and the
support files necessary. The folder can simply be copied onto
a server that simply exports part of the file-system (e.g.
Apache). Examples of use within twisted will follow later.
