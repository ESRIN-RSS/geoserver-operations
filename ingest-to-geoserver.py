import subprocess
import os
import difflib
import argparse
import json
import ast
# from geoserver.catalog import Catalog

def setup_cmd_args():
    """Setup command line arguments."""
    parser = argparse.ArgumentParser(description="Ingest layers and styles to Geoserver and associate them.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("root_dir", help="The root directory containing data to check")
    parser.add_argument("layer_name", help="Find by layer name")
    parser.add_argument("geoserver", help="Geoserver server")
    parser.add_argument("--workspace", help="Set Workspace manually")
    parser.add_argument("--gs_user", help="Geoserver username")
    parser.add_argument("--gs_passw", help="Geoserver password")
    parser.add_argument('-o', action='store_true', help="Update layer in geoserver")
    parser.add_argument('-a', action='store_true', help="Get workspace automatically")
    return parser.parse_args()


def SetGeoServerDefaultStyles(sld_file, style_name, layername, geoserver_username, geoserver_password, geoserver_server, defaultstyle, workspace):
    geoserver_url = geoserver_server + "/geoserver/rest"
    if workspace!=None:
        workspace = "/workspaces/"+workspace
    else:
        workspace = ""
    if defaultstyle:
        xml_txt='\"<layer><defaultStyle><name>'+style_name+'</name></defaultStyle></layer>\"'
    else:
        xml_txt='\"<layer><styles><style><name>'+style_name+'</name></style></styles></layer>\"'
    curl_str1='curl -v -w "%{http_code}" -u '+geoserver_username+':'+geoserver_password+' -X POST -d @'+sld_file+' -H \"content-type: application/vnd.ogc.sld+xml\" '+geoserver_url+workspace+'/styles.sld?name='+style_name
    curl_str2='curl -v -s -o /root -w "%{http_code}" -u ' + geoserver_username + ':' + geoserver_password + ' -X PUT ' + geoserver_url + '/layers/' + layername + '.xml -H \"Content-type: text/xml\" -d ' + xml_txt
    try:
        # subprocess.call(curl_str1,shell=True)
        readout1=subprocess.Popen(curl_str1, shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, bufsize=1).communicate()[0]
    except:
        print("Something went wrong with ingesting "+sld_file+"\nContinuing...")
    try:
        readout2=subprocess.Popen(curl_str2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1).communicate()[0]
    except:
        print("Something went wrong with associating " + sld_file + " style to layer: "+layername+"\nContinuing...")
    return readout1, readout2


def get_layer_workspace(geoserver_username, geoserver_password, geoserver_server, layername):
    curl_string = "curl -v -u "+geoserver_username+":"+geoserver_password+" -GET \""+geoserver_server+"/geoserver/rest/layers/"+layername+".json\""
    readout = subprocess.Popen(curl_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1).communicate()[0]
    try:
        readout = json.loads(readout)['layer']['resource']['href']
        workspace = readout.split("/")[readout.split("/").index('workspaces')+1]
    except:
        workspace = ""
    return workspace


def get_layer_name(path,root_dir):
    path_parts = path.split("/")
    if any("collection" in s for s in path_parts):
        for s in path_parts:
            if s=="collection":
                if path_parts[path_parts.index(s)-1]==path_parts[path_parts.index(s)+1]:
                    layer_name = path_parts[path_parts.index(s) + 1]
                else:
                    layer_name = path_parts[path_parts.index(s)-1] + "_" + path_parts[path_parts.index(s)+1]
    else:
        layer_name = path_parts[len(filter(None,root_dir.split("/")))+1]
    return layer_name


def check_default_style(sld_file):
    path_parts = sld_file.split("/")
    if any("defaultstyle" in s for s in path_parts):
        check_default_style = True
    else:
        check_default_style = False
    return check_default_style

def get_real_geoserver_layer_name(geoserver_username, geoserver_password, geoserver_server, layer_name):
    curl_string = "curl -v -u " + geoserver_username + ":" + geoserver_password + " -GET \"" + geoserver_server + "/geoserver/rest/layers.json\""
    readout = subprocess.Popen(curl_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1).communicate()[0]
    j=json.loads(readout)
    jentries=len(j['layers']['layer'])
    print("existing layers: " + str(jentries))
    real_names_list = []
    for i in range(0,jentries):
        real_layer_name = json.loads(readout)['layers']['layer'][i]['name']
        similarity = difflib.SequenceMatcher(None, layer_name, real_layer_name).ratio()
        real_names_list.append((real_layer_name,similarity))
    closest_real_name = sorted(real_names_list,key=lambda x: x[1], reverse=True)[0][0]
    return closest_real_name

def get_layer_name_on_dir(path, layer_name):
    closest_real_name=["","",""]
    try_layername_A = []
    try_layername_B = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith("SVG.prop"):
                svg_file = os.path.join(root, file)
                trylayername = get_layer_name(svg_file, root)
                similarity = difflib.SequenceMatcher(None, layer_name, trylayername).ratio()
                try_layername_A.append((trylayername,similarity,os.path.dirname(svg_file)))
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            trylayername = dir
            similarity = difflib.SequenceMatcher(None, layer_name, trylayername).ratio()
            try_layername_B.append((trylayername,similarity,os.path.join(root,dir)))
    closest_real_name_A = sorted(try_layername_A,key=lambda x: x[1], reverse=True)[0]
    closest_real_name_B = sorted(try_layername_B,key=lambda x: x[1], reverse=True)[0]
    # print("tryA: "+closest_real_name_A[0]+str(closest_real_name_A[1]))
    # print("tryB: "+closest_real_name_B[0]+str(closest_real_name_B[1]))
    if closest_real_name_A[1]>=0.84 or closest_real_name_B[1]>=0.84:
        if closest_real_name_A[1]>=closest_real_name_B[1]:
            closest_real_name = closest_real_name_A
        else:
            closest_real_name = closest_real_name_B
    return closest_real_name[0], closest_real_name[2]

if __name__ == '__main__':
    args = setup_cmd_args()
    if not args.root_dir.startswith('/'):
        logging.critical('root_dir parameter must be an absolute path')
        exit(1)
    if args.layer_name:
        path_to_layer_name = subprocess.check_output(["find", args.root_dir, "-name", args.layer_name])
        path_to_layer_name = path_to_layer_name.replace('\n', '').replace('\r', '')
        if path_to_layer_name=="":
            a,path_to_layer_name = get_layer_name_on_dir(args.root_dir, args.layer_name)
        if path_to_layer_name!="":
            sld_file = subprocess.check_output(["find", path_to_layer_name, "-name", args.layer_name+".sld"])
            sld_file = sld_file.replace('\n', '').replace('\r', '')
            if sld_file=="":
                print("INGEST TO GEOSERVER AND ASSIGN TO LAYER: No SLD file found for layer " + args.layer_name)
            else:
                layer_name = args.layer_name
                default = check_default_style(sld_file)
                if args.a:
                    ws = get_layer_workspace(args.gs_user, args.gs_passw, args.geoserver,
                                             layer_name)
                else:
                    ws = args.workspace
                r1, r2 = SetGeoServerDefaultStyles(sld_file, layer_name, layer_name, args.gs_user,
                                                   args.gs_passw,
                                                   args.geoserver, default, ws)
                print("INGEST TO GEOSERVER AND ASSIGN TO LAYER: " + layer_name+ ", workspace: " + ws + ", http code for ingestion: "+r1+ ", http code for assignment: "+r2)
    else:
        for root, dirs, files in os.walk(args.root_dir):
            for file in files:
                if file.endswith(".sld"):
                    sld_file=os.path.join(root,file)
                    layer_name = get_layer_name(sld_file, args.root_dir)
                    layer_name = get_real_geoserver_layer_name(args.gs_user, args.gs_passw, args.geoserver,
                                                               args.layer_name)
                    default = check_default_style(sld_file)
                    if args.a:
                        ws = get_layer_workspace(args.gs_user, args.gs_passw, args.geoserver, layer_name)
                    else:
                        ws = args.workspace
                    r1, r2 = SetGeoServerDefaultStyles(sld_file, layer_name, layer_name, args.gs_user, args.gs_passw,
                                               args.geoserver, default, ws)
                    print("INGEST TO GEOSERVER AND ASSIGN TO LAYER: " + layer_name + ", workspace: " + ws + ", http code for ingestion: " + r1 + ", http code for assignment: " + r2)

