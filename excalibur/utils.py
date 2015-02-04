# -*- coding: utf-8 -*-
"""
Cross-classes utils
"""
import hashlib
import traceback
import re
from excalibur.exceptions import WrongSignatureError

ALL_KEYWORD = "all"
PLUGIN_NAME_SEPARATOR = "|"
SOURCE_SEPARATOR = ","


def add_args_then_encode(x, y, arguments):
    """
    sha1checks are made on aggregated Strings. The process is used
    in two spots. When checks regarding the sources.yml file are done
    and in the case where allowed sources cannot be deduced from query
    arguments but must be be obtained by checking apikeys directly in all
    sources.
    """
    def add_args(x, args):
        """
        add arguments to main key before encoding
        """
        for argument in args:
            x += (argument + arguments[argument])
        return x

    def encode(x):
        """
        encode full string
        """

        return hashlib.sha1(x.encode("utf-8")).hexdigest()

    return encode(add_args(x, y))


def get_api_keys(entry, arguments):
    """
    """
    keys = []
    api_keys = []

    if type(entry['apikey']) is list:
        for k in entry['apikey']:
            keys.append(k)
    elif type(entry['apikey']) is str:
        keys.append(entry['apikey'])

    for key in keys:
        api_key = add_args_then_encode(key,
                                       sorted(arguments),
                                       arguments)
        if api_key not in api_keys:
            api_keys.append(api_key)

    return api_keys


def sources_list_or_list(source):
    """
    """
    return list(source.split(SOURCE_SEPARATOR)) if\
        SOURCE_SEPARATOR in source else [source]


def all_sources_or_sources_list_or_list(source, sources):
    """
    """
    return list(sources.keys())\
        if source == ALL_KEYWORD else sources_list_or_list(source)


def is_simple_request(source, sources):
    """
    """
    return source != ALL_KEYWORD and\
        SOURCE_SEPARATOR not in source


def is_simple_request_and_source_not_found(source, sources):
    """
    """
    return is_simple_request(source, sources) and source not in sources.keys()


def ip_found_in_sources(source, sources, request_ip):
    """
    """
    ip_authorized = True

    targeted_sources = []
    if is_simple_request(source, sources):
        targeted_sources = [sources[source].get('ip', [])]
    else:
        targeted_sources = [it["ip"] for
                            it in sources.values() if "ip" in
                            list(it.keys())]
    for ip_list in targeted_sources:
        if not [ip for ip in ip_list if re.match(ip, request_ip)]:
            ip_authorized = False
    return ip_authorized


def get_api_keys_by_sources(sources, targets):
    """
    """
    def get_keys(x):
        if type(sources[x]["apikey"]) is list:
            return sources[x]["apikey"]
        else:
            return[sources[x]["apikey"]]

    return {target: get_keys(target) for target in targets}

def get_data(plugin, f_name, parameters, query):
     f = getattr(plugin, f_name)
     return f(parameters, query.arguments)
 
def get_sources_for_all(signature, data_project,
                                 arguments, check_signature):

    apikey_present = [it["apikey"]
                      for it in list(data_project["sources"].values())
                      if "apikey" in list(it.keys())]

    if apikey_present and check_signature:

        targeted_sources = {}

        for name, value in data_project["sources"].items():

            api_keys = get_api_keys(value, arguments)

            if signature in api_keys:
                targeted_sources[name] = value

        if not targeted_sources:
            raise WrongSignatureError(signature)

        return targeted_sources

    else:
        return data_project["sources"]


def format_error(query, e, parameters_index):
    return {'source': query.source, 'ressource': query.ressource,
            'method': query.method,
            'arguments': query.arguments,
            'parameters_index': parameters_index,
            'error': e.__class__.__name__,
            'error_message': str(e)
            }

def clean_plugin_name(plugin_name):
    return plugin_name[plugin_name.index(PLUGIN_NAME_SEPARATOR) + 1:]

def set_plugin_name(plugin_name):
    return clean_plugin_name(plugin_name) if\
          separator_contained(plugin_name) else plugin_name
          
def separator_contained(plugin_name):
    return PLUGIN_NAME_SEPARATOR in plugin_name

def plugin_data_format(plugin_data, data, bool, raw_plugin_name, plugin_name):
    if plugin_data is not None:
        if bool:
            data[raw_plugin_name] = plugin_data
        else:
            data[plugin_name] = plugin_data
    return data

def get_data_or_errors(plugin_loader,
                       plugin_name,
                       query,
                       parameters_sets,
                       data,
                       errors
                       ):
        f_name = query.function_name
        raw_plugin_name = plugin_name
        separated = separator_contained(plugin_name)
        plugin_name = set_plugin_name(plugin_name)
        plugin = plugin_loader.get_plugin(plugin_name)
        for index, parameters in enumerate(parameters_sets):
            # Initialize returned data to None
            plugin_data = None
            if not hasattr(plugin, f_name):
                continue  # Ressource/method not implemented in plugin
            # Get data
            try:
                plugin_data = get_data(plugin, f_name, parameters, query)
            # Or register exception
            except Exception as e:
                errors[plugin_name] = format_error(query, e, index)
            # Register data by plugin name
            data = plugin_data_format(plugin_data, data, separated,
                                      raw_plugin_name, plugin_name)
        return data, errors
            
