# TODO

- Work with umap to turn vectors into data points. For global i think two methods, one where it streams the whole db in to get a huge set of data points, and a second where it uses the transform to add a small amount of data.

- Work with spotify api to take a playlist link and push those to track handler. Also figure out how to push a playlist to umap to get a localized playlist cluster. Likely could do this by passing the playlist, and then selecting all vectors matching isrcs again. Then feed into umap and returns an array of coords

- TLDR
    - UMAP func using total DB embeds
    - UMAP func using single data point compared to the db vectors
    - UMAP func using playlist
    - spotify playlist link compatibility, push to trackhandler
        - Note will need endpoint for this
        - note, somehow need to keep playlist in memory while all this happens? Don't save anything. I assume the flow will be user dumps link -> we query link and push to trackhandler to get the info and push to Tracks table -> Embed script embeds as it goes, run a check that sees whether all isrcs in playlist are embdedded or not for user status - > After all tracks embedded, pass to umap -> with data points pass to frontend and display.

     