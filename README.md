# slideskokaren
Presentation Baker from RST to HTML.

Describe slides using a (very slightly) customized dialect of
RestructuredText. Convert them into a HTML/CSS/JS bundle for 
use on a web-server. The style baked into the presentations is
cloned from the course materials on http://mechani.se

## The example

For a quick demo `bin/convert.py example/slides.rst example/`. The source in 
the examples folder is augmented with slides.html and the
support files necessary. The folder can simply be copied onto
a server that simply exports part of the file-system (e.g.
Apache). Examples of use within twisted will follow later.

To switch from all-slides to the javascript slideshow pass style=slideshow
to the page: e.g. index-43.html?style=slideshow.

## Dependencies

The only dependency should be docutils for the RST parser. Install
using your favourite Python package manager, e.g. `pip install docutils`.

I left the logo out of the distribution ('tis not my copyright to 
share) - the standard copy is white on transparent, just overwrite the
support/logo.svg with the correct file.
