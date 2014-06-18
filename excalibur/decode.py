# -*- coding: utf-8 -*-
"""
Module qui permet de gerer l'encodage de certains arguments. Comme par exemple,
l'encodage en base64 pour palier au probleme de
caracteres speciaux non geres par
les urls.
"""
from excalibur.exceptions import ArgumentError, DecodeAlgorithmNotFoundError
import base64


class DecodeArguments(object):

    """
    Classe contenant les differents algorithmes de decodage.

    Pour implementer un nouvel algorithme, une methode suivant la
    regle de nommage suivante decode_nomalgo doit recevoir la
    valeur en argument. Et retourner la valeur decodee.
    """

    def __init__(self, query, ressources):
        self.ressources = ressources
        self.ressource = query.ressource
        self.method_name = query.method
        self.arguments = query.arguments

    def __call__(self):
        """
        Pour chacun des arguments passes, regarde s'il doit etre decode.
        Et si c'est le cas, appelle la methode correspondante.
        """
        if self.ressource not in self.ressources.keys():
            raise ArgumentError("ressource not found")
        
        ressource = self.ressources[self.ressource]
        
        # the check is optionnal, it occurs only if there is an entry
        # "arguments
        if "arguments" in ressource[self.method_name].keys():
            try:
                arguments = ressource[self.method_name]["arguments"]
                if arguments:
                    for argument_name in self.arguments:
                        if "encoding" in arguments[argument_name]:
                            algo = arguments[argument_name]["encoding"]
                            method = getattr(self, "decode_" + algo)
                            self.arguments[argument_name] = method(
                                self.arguments[argument_name])
            except KeyError:
                raise ArgumentError('key not found')
            except AttributeError:
                raise DecodeAlgorithmNotFoundError(algo)

    def decode_base64(self, value):
        """
        Implemente le decodage base64.
        """

        # base64 decoding returns bytestrings
        decoded_value = base64.b64decode(value).decode("utf-8")
        return decoded_value
