
#!/bin/sh
set -e 
echo "copying dependencies"
snap_name="oai-mme"
#python_packages="pyrsistent cassandra flask itsdangerous werkzeug click jinja2 markupsafe requests flask_restplus aniso8601 pytz jsonschema jsonschema-3.2.0.dist-info attr importlib_metadata importlib_resources importlib_metadata-1.7.0.dist-info importlib_resources-1.5.0.dist-info zipp-3.1.0.dist-info"
python_packages="pyrsistent flask itsdangerous werkzeug click jinja2 markupsafe requests flask_restplus aniso8601 pytz jsonschema jsonschema-3.2.0.dist-info attr importlib_metadata importlib_resources importlib_metadata-1.7.0.dist-info importlib_resources-1.5.0.dist-info zipp-3.1.0.dist-info"
python_files="zipp.py six.py"

for package in $python_packages; do
    echo $package
    cp -r $HOME/mosaic5g/store/snaps/$snap_name/parts/openapi/install/lib/python3.6/site-packages/$package $HOME/mosaic5g/store/snaps/$snap_name/prime/

  #  cp -r $HOME/.local/lib/python3.6/site-packages/$package \
   #     $HOME/mosaic5g/store/snaps/$snap_name/prime/
done
for file in $python_files; do
    echo $file
    cp -r $HOME/mosaic5g/store/snaps/$snap_name/parts/openapi/install/lib/python3.6/site-packages/$file $HOME/mosaic5g/store/snaps/$snap_name/prime/
    
    #cp $HOME/.local/lib/python3.6/site-packages/$file \
    #    $HOME/mosaic5g/store/snaps/$snap_name/prime/
done


