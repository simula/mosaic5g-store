
#!/bin/sh
set -e 
echo "copying dependencies"

python_packages="pyrsistent cassandra flask itsdangerous werkzeug click jinja2 markupsafe requests flask_restplus aniso8601 pytz jsonschema jsonschema-3.2.0.dist-info attr importlib_metadata importlib_resources importlib_metadata-1.7.0.dist-info importlib_resources-1.5.0.dist-info zipp-3.1.0.dist-info"
python_files="zipp.py six.py"

for package in $python_packages; do
    echo $package
    cp -r $HOME/.local/lib/python3.6/site-packages/$package \
        $HOME/mosaic5g/store/snaps/oai-hss/prime/
done
for file in $python_files; do
    echo $file
    cp $HOME/.local/lib/python3.6/site-packages/$file \
        $HOME/mosaic5g/store/snaps/oai-hss/prime/
done


