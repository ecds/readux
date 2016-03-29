/**

Basic Zotero Web API Javascript client.

Uses https://github.com/jpillora/jquery.rest for API interaction.

Zotero Web API documentation:
https://www.zotero.org/support/dev/web_api/v3/basics


*/

function ZoteroClient(zotero_options) {
    this.zotero_options = zotero_options;
    this.client = new $.RestClient('https://api.zotero.org/', {
        // override default request method to set custom headers
        request: function(resource, options) {
            // pass in user's zotero token/key as a parameter
            options.data.key = zotero_options.token;
            options.headers = {
                'Zotero-API-Version': 3,

                // 'Authorization': 'Bearer ' + zotero_options.token,
                // NOTE: auth header doesn't work - not allowed on
                // cross-domain request:
                //   "Request header field Authorization is not allowed by
                //    Access-Control-Allow-Headers in preflight response."

                // Using key parameter for access instead.
            }
            return $.ajax(options);
        }
    });
    // add an items end point (rename to user_items, maybe?)
    this.client.add('items', {'url': 'users/' + this.zotero_options.user_id + '/items'});
}

ZoteroClient.prototype.search = function(search_term, callback) {
    // use zotero api to search for items; currently user library and
    // keyword search only. Takes a callback method to do something with the data.
    var request = this.client.items.read({'q': search_term}).done(callback);
    // request.done(function(data, textstatus, xhrObject) {
    //     callback(data);
    // });
}

ZoteroClient.prototype.data_for_autocomplete = function(items) {
    // convert zotero item data into a simplified dict format
    // for easy use in an autocomplete
    var i = 0, data = [], item, item_data, desc;
    for (i = 0; i < items.length; i++) {
        item = items[i];
        item_data = {
            id: item.key,
            title: item.data.title,
        };
        desc = [];
        if (item.meta.creatorSummary || item.meta.parsedDate) {
            if (item.meta.creatorSummary) {
                desc.push(item.meta.creatorSummary);
            }
            if (item.meta.parsedDate) {
                desc.push(item.meta.parsedDate);
            }
        }
        if (desc.length == 0 && item.data.url) {
            desc.push(item.data.url);
        }
        item_data.description = desc.join('\n');
        data.push(item_data);
    }
    return data;
}

ZoteroClient.prototype.autocomplete_search = function(search_term, callback) {
    // autocomplete method to search for a term and convert api data into
    // simplified dictionary form.  Runs a callback on the converted data.
    var client = this;
    this.search(search_term, function(data) {
        callback(client.data_for_autocomplete(data));
    });
}


ZoteroClient.prototype.get_item = function(id, format, include, callback) {
    /* Get a single zotero citation item.
    Format and include parameters as described in the Zotero documentation:
    https://www.zotero.org/support/dev/web_api/v3/basics#read_requests

    (user items only for now)
    */
    var request = this.client.items.read(id, {format: format, include: include});
    request.always(function(xhrObject) {
        // non-json content doesn't seem to fire the done action,
        // so add the callback here for non-json content
        if (format != 'json' && xhrObject.readyState == 4) {
            callback(xhrObject.responseText);
        }
    });
    request.done(function(data, textstatus, xhrObject) {
        callback(data);
    });

}


