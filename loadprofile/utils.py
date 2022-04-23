
# Enums


class ResidentialBuildingType:
    House = "house"
    Apartment = "apartment"


class ProfileType:
    Residential = 'h0'
    Commercial = 'g0'


class ResidentialRating:
    A = 'a'
    B = 'b'
    C = 'c'
    D = 'd'
    E = 'e'
    F = 'f'
    G = 'g'


class CommercialRating:
    Office = 'office'
    Hotel = 'hotel_garni'
    Retailer = 'retailer'
    Workshop = 'workshop'
    productionSite = 'production_site'
    CommercialNonfood = 'commercial_nonfood'
    RetailerNonfood = 'non_food_retailer'
    Bakery = 'bakery'


# Exceptions

class LoadProfileException(Exception):
    pass

class UnknownLoadProfileType(LoadProfileException):
    pass

class InvalidConsumptionRating(LoadProfileException):
    pass



