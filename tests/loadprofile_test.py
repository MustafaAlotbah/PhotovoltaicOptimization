import loadprofile
import matplotlib.pyplot as plt
import numpy as np


# simple plot for working day, saturday, sunday
if __name__ == "__main__":
    fig, ax = plt.subplots(2)
    fig.set_size_inches(16, 12)

    #
    # ------------ Residential profile
    #
    # Saturday is offset by 3 for day < 152
    #                       4 for day >= 152 for residential profiles

    # parameters
    profile = loadprofile.ProfileType.Residential
    building_type = loadprofile.ResidentialBuildingType.Apartment
    warm_water_electrical = True
    num_people = 3

    # plotting
    ax[0].set_title("Residential profile (3 Residents, Apartment, Water pump)")
    profile_winter = np.array([loadprofile.by_day_of_year(i,
                                                          profile=profile,
                                                          building_type=building_type,
                                                          is_warm_water_electric=warm_water_electrical,
                                                          number_of_residents=num_people,
                                                          ) for i in range(2, 5)]).flatten()
    profile_trans = np.array([loadprofile.by_day_of_year(i,
                                                         profile=profile,
                                                         building_type=building_type,
                                                         is_warm_water_electric=warm_water_electrical,
                                                         number_of_residents=num_people,
                                                         ) for i in range(91+2, 91+5)]).flatten()
    profile_summer = np.array([loadprofile.by_day_of_year(i,
                                                          profile=profile,
                                                          building_type=building_type,
                                                          is_warm_water_electric=warm_water_electrical,
                                                          number_of_residents=num_people,
                                                          ) for i in range(182+3, 182+6)]).flatten()
    ax[0].plot(profile_winter, label="Winter", color="tab:blue")
    ax[0].plot(profile_trans, label="Transitional season", color="orange")
    ax[0].plot(profile_summer, label="Summer", color="tab:red")
    ax[0].legend()
    ax[0].set_xticks([i for i in range(0, 24 * 3, 6)])
    ax[0].grid()

    #
    # ------------ Commercial profile
    #

    # parameters
    profile = loadprofile.ProfileType.Commercial
    rating = loadprofile.CommercialRating.Bakery
    area = 25

    # plotting
    ax[1].set_title("Commercial profile (Bakery with an area of 25m²)")
    profile_winter = np.array([loadprofile.by_day_of_year(i,
                                                          profile=profile,
                                                          rating=rating,
                                                          area=area
                                                          ) for i in range(6, 9)]).flatten()
    profile_trans = np.array([loadprofile.by_day_of_year(i,
                                                         profile=profile,
                                                         rating=rating,
                                                         area=area
                                                         ) for i in range(91+6, 91+9)]).flatten()
    profile_summer = np.array([loadprofile.by_day_of_year(i,
                                                          profile=profile,
                                                          rating=rating,
                                                          area=area
                                                          ) for i in range(182+6, 182+9)]).flatten()

    ax[1].plot(profile_winter, label="Winter", color="tab:blue")
    ax[1].plot(profile_trans, label="Transitional season", color="orange")
    ax[1].plot(profile_summer, label="Summer", color="tab:red")
    ax[1].legend()
    ax[1].set_xticks([i for i in range(0, 24 * 3, 6)])
    ax[1].grid()

    fig.suptitle("Load profiles by the BDEW")

    for a in ax:
        a.set_xlabel("Hour of day (Working day, Saturday, Sunday)")
        a.set_ylabel("Load power [W]")

    plt.show()

