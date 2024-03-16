'use strict';
{
  const pollingInterval = 4000;

  const logElementId = 'syncdb-log';

  const logElement =
    document.getElementById(logElementId);

  const constants =
    document.getElementById('syncdb-constants').dataset;

  function pollLog() {
    const logText = logElement.textContent.trim();

    const lastLine = logText
      .substring(
        logText.lastIndexOf('\n') + 1
      )
      .toLowerCase();

    if (lastLine.includes('[job completed]')) {
      return;
    }

    fetch(constants.logUrl, {headers: {'Accept': 'text/plain'}})
      .then(
        response => {
          if (response.status == 200) {
            return response.text();
          }
          return Promise.reject();
        }
      )
      .then(
        logText => {
          logElement.textContent = logText.trim();
          logElement.scrollTo(0, logElement.scrollHeight);
          setTimeout(pollLog, pollingInterval);
        }
      );

  }

  setTimeout(pollLog, pollingInterval);
}
