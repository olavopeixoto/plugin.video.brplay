# -*- coding: utf-8 -*-

import json
import sys
import urlparse
import buggalo

buggalo.GMAIL_RECIPIENT = 'brplayissues@gmail.com'

try:

    params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))

    #Parameters
    action = params.get('action')

    id_globo_videos = params.get('id_globo_videos')

    id_cms = params.get('id_cms')

    id = params.get('id')

    kind = params.get('kind')

    slug = params.get('slug')

    letter = params.get('letter')

    id_sexyhot = params.get('id_sexyhot')

    meta = params.get('meta')

    provider = params.get('provider')

    metaJson = json.loads(meta) if meta is not None else None

    isFolder = params.get('isFolder')

    url = params.get('url')

    page = params.get('page')

    q = params.get('q')

    category = params.get('category')

    program_id = params.get('program_id')

    date = params.get('date')

    poster = params.get('poster')

    bingewatch = (params.get('bingewatch') or 'false').lower() == "true"

    children_id = params.get('children_id')

    state = params.get('state')

    region = params.get('region')

    subcategory = params.get('subcategory')

    #Actions

    if action is None:
        from resources.lib.indexers import navigator
        navigator.navigator().root()

    elif action == 'settings':
        from resources.lib.indexers import navigator
        navigator.navigator().openSettings()

    elif action == 'clear':
        from resources.lib.indexers import navigator
        navigator.navigator().clear_cache()

    elif action == 'clearAuth':
        from resources.lib.indexers import navigator
        navigator.navigator().clear_credentials()

    elif action == 'login':
        from resources.lib.indexers import navigator
        navigator.navigator().cache_auth()

    elif action == 'refresh':
        from resources.lib.modules import control
        control.refresh()

    elif action == 'searchMenu':
        from resources.lib.indexers import navigator
        navigator.navigator().searchMenu()

    elif action == 'search':
        from resources.lib.indexers import navigator
        navigator.navigator().search(q, page)

    elif action == 'featured':
        from resources.lib.indexers import vod

        vod.Vod().get_extras()

    elif action == 'favorites':
        from resources.lib.indexers import vod

        vod.Vod().get_favorites()

    elif action == 'addFavorites':
        from resources.lib.indexers import vod

        vod.Vod().add_favorites(id_globo_videos)

    elif action == 'delFavorites':
        from resources.lib.indexers import vod

        vod.Vod().del_favorites(id_globo_videos)

    elif action == 'watchlater':
        from resources.lib.indexers import vod

        vod.Vod().get_watch_later()

    elif action == 'addwatchlater':
        from resources.lib.indexers import vod

        vod.Vod().add_watch_later(id_globo_videos)

    elif action == 'delwatchlater':
        from resources.lib.indexers import vod

        vod.Vod().del_watch_later(id_globo_videos)

    elif action == 'watchhistory':
        from resources.lib.indexers import vod

        vod.Vod().get_watch_history()

    elif action == 'liveChannels':
        from resources.lib.indexers import live
        live.Live().get_channels()

    elif action == 'vodChannels':
        from resources.lib.indexers import vod
        vod.Vod().get_vod_channels_directory()

    ## COMMON
    elif action == 'showdates':
        from resources.lib.indexers import vod
        page = page or 1
        vod.Vod().get_program_dates(program_id, poster, provider)

    elif action == 'openvideos' and date:
        from resources.lib.indexers import vod
        vod.Vod().get_videos_by_program_date(program_id, date, poster, provider, bingewatch)


    ###GLOBOSAT PLAY

    #PREMIER FC
    elif action == 'playlive' and isFolder == True or isFolder == 'True':
        from resources.lib.indexers import live
        live.Live().get_subitems(metaJson)

    #LIVE CHANNELS
    elif action == 'playlive' and provider == 'globosat':
        from resources.lib.modules.globosat import player
        player.Player().playlive(id_globo_videos, meta)

    #VOD CHANNELS
    elif action == 'openchannel' and provider == 'globosat':
        from resources.lib.indexers import vod
        if slug == 'combate':
            vod.Vod().get_channel_categories(slug=slug)
        elif id_cms:
            vod.Vod().get_channel_programs(channel_id=id_cms)

    elif action == 'openvideos' and provider == 'globosat':
        from resources.lib.indexers import vod
        page = page or 1
        vod.Vod().get_videos_by_program(program_id, int(page), poster, 'globosat', bingewatch)

    elif action == 'playvod' and provider == 'globosat':
        from resources.lib.modules.globosat import player

        player.Player().playlive(id_globo_videos, meta)

    elif action == 'opencategory' and provider == 'combate':
        from resources.lib.indexers import vod
        vod.Vod().get_events_by_categories(category)

    elif action == 'openevent' and provider == 'combate':
        from resources.lib.indexers import vod
        vod.Vod().get_event_videos(category, url)

    elif action == 'openfighters':
        from resources.lib.indexers import vod
        vod.Vod().get_fighters(letter)

    elif action == 'openfighter':
        from resources.lib.indexers import vod
        vod.Vod().get_fighter_videos(slug, page)

    elif action == 'openfeatured' and provider == 'globosat':
        from resources.lib.indexers import vod
        vod.Vod().get_featured()

    elif action == 'openextra' and provider == 'globosat':
        from resources.lib.indexers import vod
        vod.Vod().get_track(id, kind)


    ###GLOBO PLAY

    elif action == 'playlive' and provider == 'globoplay':
        from resources.lib.modules.globoplay import player

        player.Player().play_stream(id_globo_videos, meta)

    elif action == 'openchannel' and provider == 'globoplay':
        from resources.lib.indexers import vod
        if slug == 'futura':
            vod.Vod().get_channel_categories(slug=slug)
        else:
            vod.Vod().get_channel_categories()

    elif action == 'openextra' and provider == 'globoplay':
        from resources.lib.indexers import vod
        vod.Vod().get_videos_by_category(category, int(page or 1), poster)

    elif action == 'opencategory' and provider == 'futura':
        from resources.lib.indexers import vod
        vod.Vod().open_futura_menu(category)

    elif action == 'opencategory' and provider == 'globoplay' and subcategory is not None:
        from resources.lib.indexers import vod
        vod.Vod().get_programs_by_subcategory(category, subcategory)

    elif action == 'opencategory' and provider == 'globoplay':
        from resources.lib.indexers import vod
        vod.Vod().get_programs_by_category(category)

    elif action == 'openlocal' and region is not None and provider == 'globoplay':
        from resources.lib.indexers import vod
        vod.Vod().get_programs_by_region(region)

    elif action == 'openlocal' and state is not None and provider == 'globoplay':
        from resources.lib.indexers import vod
        vod.Vod().get_regions(state)

    elif action == 'openlocal' and provider == 'globoplay':
        from resources.lib.indexers import vod
        vod.Vod().get_states()

    elif action == 'openvideos' and provider == 'globoplay':
        from resources.lib.indexers import vod
        page = page or 1
        vod.Vod().get_videos_by_program(program_id, int(page), poster, 'globoplay', bingewatch)

    elif action == 'playvod' and provider == 'globoplay':
        from resources.lib.modules.globoplay import player
        player.Player().play_stream(id_globo_videos, meta)

    elif action == 'playvod' and provider == 'globoplay':
        from resources.lib.modules.globoplay import player
        player.Player().play_stream(id_globo_videos, meta, children_id)

    elif action == 'open4k' and provider == 'globoplay':
        from resources.lib.indexers import vod
        vod.Vod().get_4k()


    ###SEXY HOT

    elif action == 'openchannel' and provider == 'sexyhot':
        from resources.lib.modules.sexyhotplay import indexer

        indexer.indexer().get_categories()

    elif action == 'getVideos' and provider == 'sexyhot':
        from resources.lib.modules.sexyhotplay import indexer

        indexer.indexer().get_videos(url)

    elif action == 'playvod' and provider == 'sexyhot':
        from resources.lib.modules.sexyhotplay import player

        player.Player().play_vod(id_sexyhot, meta)

except Exception:
    buggalo.onExceptionRaised()