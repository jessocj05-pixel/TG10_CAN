    def finish_activity(self, text):

        """
        Hide the progress indicator after the operation completes.
        """

        self.activity_status.setText(
            text
        )

        self.activity_progress.setValue(
            100
        )

        self.activity_progress.hide()