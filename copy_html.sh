# copy html content from sphinx documentation to docs folder for githubpages rendering
rm -r docs/* && \
cp -r sphinx/_build/html/* docs



