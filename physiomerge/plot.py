from common import Command, copy_dict, find_indices
import numpy as np

import matplotlib.pyplot as plt
from scipy import signal


class Plot(Command):
    def __init__(self, command: dict) -> None:
        super().__init__(command)
        self.marker = command.get("index", "")
        self.show = command.get("show", False)
        self.title = command.get("title", "")
        self.y_axis = command.get("y_axis", "")
        self.x_axis = command.get("x_axis", "")
        self.save = command.get("save", "")
        self.comments = command.get("comments", [])

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validates the Measurement instance to ensure it meets the required criteria.
        """
        is_valid = True

        required_str = ["channel", "marker", "title", "y_axis", "x_axis", "save","comments"]
        if not self.check_type_inner(required_str, [str]):
            is_valid = False

        required_bool = ["show"]
        if not self.check_type_inner(required_bool, [bool]):
            is_valid = False

        try:
            self.equal_size(["name", "title", "show", "save"])
            self.equal_size(["channel", "marker", "y_axis", "x_axis"])
            self.equal_size(["comments"])
        except ValueError as e:
            self.print("error", f"Validation failed: {e}")
            is_valid = False

        if is_valid:
            self.string_upper(["name", "channel", "marker", "title","comments"])

        # Validate using the base class
        if not super().validate() or not is_valid:
            self.print("error", f"{self.type} class is not valid")
            return False

        self.print("debug", f"{self.type} class is valid")
        return True

    def execute(
        self, variables: dict[str, list[dict[str, any]]]
    ) -> dict[str, list[dict[str, any]]]:
        """
        Executes the Measurement command on the provided variables.
        """
        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        for name, show, title, save in zip(self.name, self.show, self.title, self.save):
            # Safely get the list of people
            for person_ in variables.get(name, []):
                title_ = title
                save_ = save
                person = copy_dict(person_)
                self.print("debug", f"{person["FILENAME"]}, {person["COLUMNS"]}")

                # if title != "":
                #    save_data = header + "\n" + save_data
                title_ = title_.replace("{NAME}", name)
                title_ = title_.replace("{FILENAME}", person["FILENAME"])
                save_ = save_.replace("{NAME}", name)
                save_ = save_.replace("{FILENAME}", person["FILENAME"])

                person = self.plot(person, show, title_, save_, self.comments)
        return variables

    def plot(self, person, show, title, save, comments) -> dict[str, any]:
        """
        Performs the specified measurement operation on the given person's data.
        """
        self.print(
            "debug",
            f"{self.type} of {person['FILENAME']} - ",
            self.debug_data(
                channels=self.channel,
                person = person["FILENAME"],
                show = show, 
                title = title,
                save = save,
                comments = comments
            ),
        )

        # if not person[channel]:
        #    self.print("warning", f"empty data channel for {person["FILENAME"]}")

        title = title.replace("{FILENAME}", person["FILENAME"])
        num_rows = len(self.channel)
        fig, axes = plt.subplots(
            num_rows, 1, figsize=(10, 2 * num_rows), sharex=True, sharey=False
        )
        axes = [axes] if num_rows == 1 else axes
        # axes = axes.flatten()
        fs = person["FREQUENCY"]

        # Prepare resampled time axis
        target_fs = 50
        n_samples = person["DATA"].shape[0]
        original_time = np.arange(n_samples) / fs
        duration = n_samples / fs
        n_samples_resampled = int(duration * target_fs)
        resampled_time = np.arange(n_samples_resampled) / target_fs

        for ax, name, y_name, x_name, marker in zip(
            axes, self.channel, self.y_axis, self.x_axis, self.marker
        ):
            self.print(
                "index",
                f"{self.type} of {person['FILENAME']} - ",
                self.debug_data(name=name, y_name=y_name, x_name=x_name, marker=marker,comments=comments)
            )
            column = None
            # Plotting Column
            try:
                column = find_indices(name, person["COLUMNS"])[0]
            except IndexError:
                ax.set_visible(False)
                self.print(
                    "warning",
                    f"DATA Could not find '{name}' for {person["FILENAME"]}, only found {person["COLUMNS"]}",
                )
                continue


            #if column is not None:
            #    values = person["DATA"][:, column]
            #    n_samples = len(values)
            #    time_axis = np.arange(n_samples) / fs
            #    ax.plot(time_axis, values, color="#5e81ac")
            if column is not None:
                values = person["DATA"][:, column]
                
                # Resample to target frequency
                if n_samples_resampled == 0:
                    self.print("warning", "visual error, data size is 0")
                    continue    

                resampled_values = signal.resample(values, n_samples_resampled)
                
                # Plot resampled data
                ax.plot(resampled_time, resampled_values, color="#5e81ac")
                if y_name != "":
                    ax.set_ylabel(y_name)
                if x_name != "":
                    ax.set_xlabel(x_name)

            # Plotting Markers
            mark = None
            try:
                if marker == "":
                    self.print("index", f"No marker provided moving on")
                    continue
                mark = find_indices(marker, person["COLUMNS"])[0]
            except IndexError:
                self.print(
                    "warning",
                    f"MARKER Could not find  '{marker}' for {person["FILENAME"]}",
                )
            else:
                self.print(
                    "index",
                    f"MARKER found as '{mark}' for {person["FILENAME"]}",
                )


                # Plotting Markers
                mask = np.array([mark in marker_list for marker_list in person["MARKERS"]])
                if mask.any():  # If any True values
                    indices = np.where(mask)[0]
                    times = indices / fs
                    ax.scatter(
                        times,
                        values[indices],
                        marker="o",
                        facecolors="none",
                        color="#5e81ac",
                        s=50,
                        zorder=5
                    )

                # Check person["MARKERS"] for this marker
                #for i, marker_list in enumerate(person["MARKERS"]):
                #    # print("marker_list", marker_list)
                #    if mark in marker_list:
                #        time = i / fs
                #        ax.scatter(
                #            time,
                #            values[i],
                #            marker="o",
                #            facecolors="none",
                #            color="#5e81ac",
                #        )

            # Plotting Comments
            if comments:

                comment_positions = []
                comment_texts = []

                for i, comm in enumerate(person["COMMENTS"]):
                    if comm in comments: 
                        position = i / fs
                        comment_positions.append(position)
                        comment_texts.append(comm)
                        self.print("index", f"Drawing comment {comm} at position {position}")

                # Plot all at once if there are comments
                if comment_positions:
                    # Get axis limits once
                    ymin, ymax = ax.get_ylim()
                    y_bottom = ymin
                    
                    # Plot all vertical lines in one call
                    ax.vlines(x=comment_positions,
                            ymin=y_bottom,
                            ymax=ymax,
                            colors="black",
                            linestyles="-",
                            linewidth=1.5)
                    
                    # Plot all text labels
                    for pos, comm in zip(comment_positions, comment_texts):
                        ax.text(x=pos,
                                y=y_bottom,
                                s=comm,
                                rotation=90,
                                va="bottom",
                                ha="center",
                                fontsize=10,
                                bbox=dict(
                                    facecolor="white",
                                    edgecolor="black",
                                    boxstyle="round,pad=0.3"
                                ))

                #for i, comm in enumerate(person["COMMENTS"]):
                #    if comm in comments:
                #        position = i/person["FREQUENCY"]
                #        self.print("index", f"Drawing comment {comm} at position {position}")
                #        ax.axvline(x=position,
                #                    color="black",
                #                    linestyle="-",
                #                    linewidth=1.5)
                #        ax.text(x=position,
                #                y=ax.ylim()[0],
                #                s=comm,
                #                rotation=90,
                #                va="bottom",                  # anchor at bottom
                #                ha="center",                  # centered on line
                #                fontsize=10,
                #                bbox=dict(
                #                    facecolor="white",
                #                    edgecolor="black",
                #                    boxstyle="round,pad=0.3"
                #                        )
                #                )
        plt.suptitle(title)
        plt.tight_layout()
        # plt.savefig(f"figures/{person["FILENAME"]}.svg")
        if save:
            plt.savefig(save)
        if show:
            plt.show()
        plt.close()

    # return person
