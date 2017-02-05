# webwatch.py

## A minimal and easy to use website monitoring script

Checks if certain parts of a website have changed in comparison to the last time
the script was called. Best to use in cronjobs.

The main function to use is `check_site(label, url, selector)`. `selector` is the CSS
selector for the website part(s) that you want to monitor. It will then scrape the website at `url`, extract its textual contents at `selector` and generate a sha256 hash from these contents. This hash will be compared with a hash that was generated at the previous run and has been loaded from a [pickle file](https://docs.python.org/3.5/library/pickle.html) *prevstates.pickle*. If it's not the same hash, a notification email will be sent.

### Example usage

```Python
import webwatch

webwatch.MAIL_SENDER = 'webwatch@example.com'
webwatch.MAIL_RECEIVER = 'notify_me@example.com'

webwatch.init()

webwatch.check_site('spiegel', 'http://www.spiegel.de/', 'div.teaser')

webwatch.finish()
```

### Requirements

* tested with Python 3
* [requests](https://pypi.python.org/pypi/requests)
* [beautifulsoup4](https://pypi.python.org/pypi/beautifulsoup4)

### License

This project is licensed under MIT License. See *LICENSE* file for the full text.
