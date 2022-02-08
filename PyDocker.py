import os,argparse
import json

# Retrieve version and update build
with open('package.json') as json_file:
    package = json.load(json_file)

parser = argparse.ArgumentParser()
parser.add_argument('-b', "--build", help="build docker.",action="store_true", default=False)
parser.add_argument('-r', "--run", help="run docker.",action="store_true", default=False)
parser.add_argument('-s', "--save", help="save docker to file.",action="store_true", default=False)
parser.add_argument('-a', "--author", help="author name (default=smartblug).",default="smartblug")
parser.add_argument('-t', "--tag", help="tag (default=latest).",default="latest")
parser.add_argument('-i', "--inc", help="just increase release build (already included with build).",action="store_true", default=False)
args = parser.parse_args()

if args.build:
    args.inc = True

if args.inc:
    package['build']=int(package['build']+1)
    print('increasing release to',package['version'],'build',package['build'])
    with open('package.json', 'w') as json_file:
        json.dump(package, json_file)

if args.build:
    print('building',args.author+'/'+package['name']+':'+args.tag)
    os.system('docker build -t '+args.author+'/'+package['name']+':'+args.tag+' .')

if args.run:
    print('running',args.author+'/'+package['name']+':'+args.tag)
    os.system('docker run -it '+args.author+'/'+package['name']+':'+args.tag)

if args.save:
    print('saving',args.author+'/'+package['name']+':'+args.tag)
    os.system('docker save -o '+package['name']+'.tar '+args.author+'/'+package['name']+':'+args.tag)    