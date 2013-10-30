import re

from flask.ext.restful import Resource

import chirp.library.album
import chirp.library.artists
import chirp.library.dropbox

import current_route
from messages import Messages


def album_to_json(album, path):
    """ Takes a chirp library albumum and path. Returns a dict of albumum attributes """
    
    result = {}
    result['path'] = path
    result['title'] = album.title()

    if album.is_compilation():
        result['compilation'] = True
        result['artist'] = 'Various Artists'
    else:
        result['compilation'] = False
        result['artist'] = album.artist_name()
    
    # build tracks
    result['tracks'] = []
    for au_file in album.all_au_files:
        track = {}
        
        # extract track number
        track['number'] = re.search('^[0-9]*', au_file.mutagen_id3['TRCK'].text[0]).group(0)

        track['title'] = au_file.tit2()
       
        if result['compilation']:
            track['artist'] = au_file.tpe1()
        result['tracks'].append(track)

    return result


class ScanDropbox(Resource):

    def dump_dropbox(self):
        drop = chirp.library.dropbox.Dropbox()
        result = []
        for path in sorted(drop._dirs):
            try:
                chirp_albums = chirp.library.album.from_directory(path, fast=True)
            except chirp.library.album.AlbumError, e:
                Messages.add_message('error', 'There was an error at %s.' % path)
                continue

            # build albums
            for album in chirp_albums:
                json = album_to_json(album, path)
                result.append(json) 

        # check for new artists
        new_artists = []
        for data in result:
            if chirp.library.artists.standardize(data['artist']) is None:
                new_artists.append(data['artist'])
                data['warning'] = True

        if new_artists:
            Messages.add_message('New artists in dropbox: %s' % '<br>'.join(new_artists), 'warning')
        
        if len(result) > 0:
            current_route.CURRENT_ROUTE = 'import'

        return result

    def get(self):
        return self.dump_dropbox()