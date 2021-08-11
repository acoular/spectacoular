conda build --py 3.7 --no-copy-test-source-files recipe.local_py37
conda build --py 3.8 --no-copy-test-source-files recipe.local_py38
cd ~/anaconda3/conda-bld/linux-64/
conda convert -p all -o .. spectacoular*


