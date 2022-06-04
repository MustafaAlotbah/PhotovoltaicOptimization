import cadaster
import matplotlib.pyplot as plt


if __name__ == "__main__":
    # inputs
    address = "Eupener Str. 270, 52076 Aachen"
    panel_width = 1.0
    panel_height = 1.63
    min_inclination = 15
    max_inclination = 45

    # request
    building = cadaster.by_address(address)
    roof_df = cadaster.get_surfaces_info(
        building,
        panel_width=panel_width,
        panel_height=panel_height,
        min_inclination=min_inclination,
        max_inclination=max_inclination,
        shadow_offset=0  # meters
    )

    # plot
    fig, axs = plt.subplots()
    axs.set_aspect('equal', 'datalim')
    axs.get_xaxis().set_visible(False)
    axs.get_yaxis().set_visible(False)

    usable_label = False
    obstacle_label = False

    for index, row in roof_df.iterrows():
        for s_index, roof_surface in enumerate(row['geometry']):
            xs, ys = roof_surface.exterior.xy
            intensity1 = 1 - min(1, abs(row['slope']/80))
            intensity2 = min(1, abs(row['orientation']/180)) * 0.5

            if s_index == 0:
                if row["slope"] < 15:
                    axs.fill(xs, ys, alpha=1, fc='tab:orange', ec='black', hatch="++", linewidth=2.0, label="Flat surface")

                else:
                    if not usable_label:
                        label = "Usable area"
                        usable_label = True
                    else:
                        label = None

                    axs.fill(xs, ys, alpha=1, fc='tab:blue', ec='black', label=label)

                    x, y = roof_surface.centroid.xy
                    x = x[0]
                    y = y[0]
                    t = axs.text(x, y, f"{row['max_num_panels']}", color="black", fontsize=22)
                    t.set_bbox(dict(facecolor='white', alpha=0.85))
            else:
                if not obstacle_label:
                    label = "Obstacle"
                    obstacle_label = True
                else:
                    label = None
                axs.fill(xs, ys, alpha=1, fc='white', ec='tab:red', hatch="xx", linewidth=2.0, label=label)

    for index, row in roof_df.iterrows():
        for rect in row['panels_positions']:
            xs, ys = list(zip(*rect))
            axs.fill(xs, ys, facecolor="black", edgecolor=(0.85, 0.8, 0.8), linewidth=2.0)

        for rect_i in range(row['num_panels_assigned']):
            rect = row['panels_positions'][rect_i]
            xs, ys = list(zip(*rect))
            axs.fill(xs, ys, facecolor="black", hatch="++", edgecolor='#f5ec42', linewidth=2.0, fill='black')

    axs.axis('off')
    plt.legend()
    plt.show()
