# Work Summary

I've condensed all of the work done in the thesis into a single script `data.py` which does everything required to do the analysis as defined in the thesis paper.

The function described here have docstrings attached, so if you open this repository in a code editor (e.g. vscode), you'll be able to see their documentation.

## Sampling
Steps 1-4 can be performed on a list of GitHub Repository URLs via the `data.active_sample` function:
```python
import data

urls = <list of URLs>
s = data.active_sample(urls, <GitHub Personal Access Token>)
```

The sample used in the research is contained in `in.json`.

If you want to get the number of commits made in the last `n` days for a single repository, the `data.commits_in_last_n_days` can be use to do that.

## Data Extraction
The data extraction is performed by running `data.py` as a script. Run `python data.py -h` to see this options.
If you want to do the data extraction with storing the data, you can use the `data.repository_stats_from_api` function. 

## Output Structure
The output data is stored in directory with the following structure:

&lt;the string passed as `-o`/`--output` option&gt;<br>
|<br>
+----&lt;repository-owner&gt;<br>
|&nbsp;&nbsp;&nbsp;&nbsp;|<br>
|&nbsp;&nbsp;&nbsp;&nbsp;+----&lt;repository-name&gt;<br>
|&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;|<br>
|&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;+----&lt;issue-number&gt;.json<br>
|&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;|<br>
|&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;+----... the remaining issues ...<br>
|&nbsp;&nbsp;&nbsp;&nbsp;+----... the remaining repository belonging the &lt;repository-owner&gt;<br>
+----... the remaining &lt;repository-owner&gt;s<br>

Reading the output of `data.py` is as simple as calling the `data.load_from_files` function with the path of the output directory. If you want to update the data in Python, and then save it back, you can call `data.save_to_files` to write the changed data to another directory.

## As `pandas.DataFrame`
The `RepositoryStats` (i.e. the resultant object from extracting or reading the data) object in Python can be converted to a `pandas.DataFrame` using the `data.repository_stats_to_df` function.