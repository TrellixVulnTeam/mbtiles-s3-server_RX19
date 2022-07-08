# mbtiles-s3-server [![CircleCI](https://circleci.com/gh/uktrade/mbtiles-s3-server.svg?style=shield)](https://circleci.com/gh/uktrade/mbtiles-s3-server) [![Test Coverage](https://api.codeclimate.com/v1/badges/c261eb01bc9446278cd3/test_coverage)](https://codeclimate.com/github/uktrade/mbtiles-s3-server/test_coverage)


Python server to on-the-fly extract and serve vector tiles from mbtiles files on S3. Javascript, maps styles, fonts, and sprites are included so you can get setup quickly, especially with OpenMapTiles mbtiles files, but these are not required to be used.

Versioning must be enabled on the underlying S3 bucket

> Work in progress. Not all features described are implemented. This document serves as a rough design spec.


## Installation

```bash
pip install mbtiles-s3-server
```

The libsqlite3 binary library is also required, but this is typically already installed on most systems. The earliest version of libsqlite3 known to work is 2012-12-12 (3.7.15).


## Example usage

1. Create or obtain an mbtiles file, for example from https://openmaptiles.org/.

2. Upload this file to S3, for example to `https://my-bucket.s3.eu-west-2.amazonaws.com/tiles.mbtiles`

3. Ensure to have a IAM user that has `s3:GetObject` and `s3:GetObjectVersion` permissions on this S3 object, for example

   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Sid": "",
               "Effect": "Allow",
               "Principal": "*",
               "Action": [
                   "s3:GetObject",
                   "s3:GetObjectVersion"
               ],
               "Resource": [
                   "arn:aws:s3:::my-bucket/tiles.mbtiles"
               ]
           }
       ]
   }   
   ```

4. Start this server, configured with the location of this object and credentials for this user - it's configured using environment variables. You can assign the tiles file any version you like, in this case, `1.0`.

   ```bash
   PORT=8080 \
   MBTILES__1__URL=https://my-bucket.s3.eu-west-2.amazonaws.com/tiles.mbtiles \
   MBTILES__1__IDENTIFIER=mytiles \
   MBTILES__1__VERSION=1.0 \
   AWS_REGION=eu-west-2 \
   AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE \
   AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
   AWS_SESSION_TOKEN="Only needed for temporary credentials" \
   HTTP_ACCESS_CONTROL_ALLOW_ORIGIN="*" \
       python -m mbtiles_s3_server
   ```

5. On your user-facing site, include HTML that loads these tiles from this server, for example to load maps from a server started as above running locally

   ```html
   <!DOCTYPE html>
   <html>
     <head>
       <meta charset="utf-8">
       <title>Example map</title>
       <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
       <script src="http://localhost:8080/v1/static/maplibre-gl@2.1.9/maplibre-gl.js"></script>
       <link href="http://localhost:8080/v1/static/maplibre-gl@2.1.9/maplibre-gl.css" rel="stylesheet">
     </head>
     <body>
       <h1>Example map</h1>
       <div id='map' style='width: 400px; height: 300px;'></div>
       <script>
       var map = new maplibregl.Map({
           container: 'map',
           style: 'http://localhost:8080/v1/styles/positron-gl-style@1.8/style.json?tiles=mytiles@1.0',
           center: [-74.5, 40],
           zoom: 9
       });
       </script>
     </body>
   </html>
   ```

   This HTML is included in this repository in [example.html](./example.html). A simple server can be started to view it by

   ```bash
   python -m http.server 8081 --bind 127.0.0.1
   ````

   and going to [http://localhost:8081/example.html](http://localhost:8081/example.html)


## For the curious, advanced, or developers of this server itself

Hosting your own vector map tiles to show them in a browser requires quite a few components:

1. **JavaScript**

   A library such as [MapLibre GL](https://github.com/maplibre/maplibre-gl-js), and your own code to run the library, and point it to a style file

2. **Style file**

   A JSON file that defines how the library should style the map tiles, and where it should find the map tiles, glyphs (fonts), and the sprite

3. **Glyphs** (fonts)

   Sets of fonts; different fonts can be used for different labels and zoom levels, as defined in the Style file

4. **Sprite**

   A single JSON index file and a single PNG file; the JSON file contains the offsets and sizes of images within the single PNG file

5. **Vector map tiles**

   A set of often hundreds of thousands of tiles each covering a different location and different zoom level. These can be distributed as a single mbtiles file, but this is not the format that the Javascript library accepts. This on-the-fly conversion from the mbtiles file to tiles is the main feature of this server.


## Licenses

The code of the server itself is released under the MIT license. However, several components included are released under separate licenses.
