# geoserver-operations
Scripts to interact with maps.eo.int geoserver
Automatically create layergroups in geoserver. This includes 2 different methods:

1) self driven organization - the script will  organize groups of layers based on the similarity between the layer names and assign a layer group name for each group based on the common characters between the layers names in the group.

   `Example: auto_group_layers.py http://maps.eo.esa.int/geoserver/rest/ --gs_user geoserver_username --gs_passw geoserver_pw --layerslist c:\temp\layerslist.txt --selfdriven --workspace APOLLO`

2) manual input - The layer list and layer group name is assigned manually in the arguments.

    `Example: auto_group_layers.py http://maps.eo.esa.int/geoserver/rest/ --gs_user geoserver_username --gs_passw geoserver_pw --layerslist c:\temp\layerslist.txt --layergroupname teste --workspace APOLLO`


    usage: auto_group_layers.py 
        [-h] [--layerslist LAYERSLIST]
        [--workspace WORKSPACE]
        [--layergroupname LAYERGROUPNAME] --gs_user
        GS_USER --gs_passw GS_PASSW [-sd]
        geoserver
    
    positional arguments:
      geoserver             Geoserver server
    
    optional arguments:
    
      -h, --help            show this help message and exit
      --layerslist LAYERSLIST
                            Folder to write/read the layer list.
      --workspace WORKSPACE
                            Set Workspace manually
      --layergroupname LAYERGROUPNAME
                            Set layergroupname manually
      --gs_user GS_USER     Geoserver username
      --gs_passw GS_PASSW   Geoserver password
      -sd, --selfdriven     Self driven organization