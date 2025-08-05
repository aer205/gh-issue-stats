# Towards Analyzing Developer Efficiency in Enterprise-Driven Open Source Projects through Commit and Issue Tracking Data

This repository specifies and provides methods for extracting metrics related to the approximation of the starting and ending of work on open issues, until they are closed. The data are intended to be used for computing issue cycle times, issue durations and for comparison against other metrics. This can then be used create benchmarks based on said metrics, like developer efficiency (how much of the issue is spent on working vs. number of people wworking?), issue durations (how long shoud issues take to complete?) etc. 

Usage of the data extraction script is described in this `README.md` file. For further details and examples, refer to the `thesis.pdf` paper.

The `out` directory is an example of the result of running the `data.py` script with sample `in.json` on 30 Jul 2025, containing data for 15640 Issues across 40 GitHub Repositories.

## Sampling
Creating a sample of active GitHub Repositories can be done using `data.active_sample`, using commits in the last `n` (default: 90) days as the activity metric:
```python
import data

urls = <list of URLs>
s = data.active_sample(urls, <GitHub Personal Access Token>)
```

If you want to get the number of commits made in the last 90 days for a single repository, the `data.commits_in_last_n_days` can be use to do that.
By default, 40 projects are selected. If you don't already has a set of URLs to analyse, this is a convenient way to create one, as the `17k_projects.csv`'s `url` column already provides a set to choose from.

## Data Extraction
The data extraction is performed by running `data.py` as a script. Run `python data.py -h` to see this options.

The following data are collected for every GitHub Issue in the GitHub repositories in the URL list:
- `number` (number) <br>
The issue number, used as an identifier for the Issue.
- `created_at` (ISO 8601 string) <br>
The date of the Issue's creation, stored in the ISO 8601 format.
- `closed_at` (ISO 8601 string) <br>
The date of the Issue's (last) closure, stored in the ISO 8601 format.
- `start_event` (string | "null") <br>
The event type of the start-of-work [1] event. Is `null` when no such event occurred.
- `started_at` (ISO 8601 string | "null") <br>
The data of the start-of-work [1] event. Is `null` when no such event occurred.
- `start_id` (number | "null") <br>
The event id of the start-of-work [1] event. Is `null` when no such event occurred.
- `finish_event` (string | "null") <br>
The event type of the end-of-work [2] event. Is `null` when no such event occurred.
- `finished_at` (ISO 8601 string | "null") <br>
The data of the end-of-work [2] event. Is `null` when no such event occurred.
- `finish_id` (number | "null") <br>
The event id of the end-of-work [2] event. Is `null` when no such event occurred.
- `state_reason` (string | "null") <br>
The reason why the Issue is closed. Is `null` when unspecified.
- `is_pull` (boolean) <br>
`true` if this Issue is a Pull Request. `false` otherwise.
- `is_squash` (boolean) <br>
`true` if this Issue is a Pull Request which was merged using squash-and-merge. `false` otherwise.

For an Issue to be included it must be created and closed within a certain time frame, specified as script inputs. By default these are 1.5 and 1 year respectively.

[1] Start-of-work: the date at which work on an Issue starts (e.g. when code starts to be written or work is distributed)

[2] End-of-work: the date at which work on an Issue ends (e.g. when the Issue is closed or a PR is merged)

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
The `RepositoryStats` (i.e. the resultant object from extracting or reading the data) object in Python can be converted to a `pandas.DataFrame` using the `data.repository_stats_to_df` function. This allows for easy interoperability with libraries like `matplotlib` to create visualizations and `numpy` for more complex mathematical operations.

## Relation to thesis work
The sample used in the research is contained in `in.json`, and the `out` directory contains the statistics used in the thesis (`thesis.pdf`).