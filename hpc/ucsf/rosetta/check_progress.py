#!/usr/bin/env python2

# The MIT License (MIT)
#
# Copyright (c) 2015 Shane O'Connor
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""\
Checks the status of a loops benchmark run.

Usage:
    check_progress.py [<benchmark_name>] [options]

Arguments:
    benchmark_name
        The name for this benchmark.  It's ok for several benchmark runs to
        have the same name.  The analysis script will automatically pick the
        most recent one when given an ambiguous name.

Options:
    --database DATABASE -d DATABASE
        By default, the script will query the database defined in the settings.conf file. This setting allows other databases to be queried.

    --summary
        Omits the progress breakdown per structure and just reports the global progress. [default: 1]

    --list
        Lists all available benchmarks in the database (identified by name) but does not print any progress report.
"""

import sys
from libraries import settings
#from libraries import database
from libraries.dataController import DataController
from libraries import colortext


def exit(message):
    sys.exit(message + '\n')


#def get_benchmark_list_by_name(database_name):
#    with database.connect(db_name = database_name) as session:
#        return [r.name for r in session.execute('SELECT DISTINCT name from benchmarks ORDER BY benchmark_id DESC')]


def get_progress(data_controller, database_name, benchmark_name):
    return data_controller.get_progress(database_name, benchmark_name)

#    try: database.test_connect(db_name = database_name)
#    except RuntimeError, error:
#        print error
#        sys.exit(1)
#
#    # Create an entry in the benchmarks table.
#    with database.connect(db_name = database_name) as session:
#
#        messages = ['']
#
#        # Use the latest benchmark's name if none was supplied
#        if not benchmark_name:
#            q = session.query(database.Benchmarks).order_by(database.Benchmarks.benchmark_id.desc())
#            if q.count() == 0:
#                exit('There is no benchmark data in the database "{0}".'.format(database_name))
#            benchmark_name = q.first().name
#            messages.append('No benchmark was selected. Choosing the most recent benchmark: "{0}".\n'.format(benchmark_name))
#
#        # Retrieve the set of benchmark runs associated the benchmark name
#        q = session.query(database.Benchmarks).filter(database.Benchmarks.name == benchmark_name)
#        if q.count() == 0:
#            exit('There is no benchmark data in the database "{0}" for benchmark "{1}".'.format(database_name, benchmark_name))
#        benchmark_runs = q.all()
#
#        # Set nstruct to be the maximum value over the runs
#        nstruct = max([b.nstruct for b in benchmark_runs])
#
#        # Retrieve the set of PDB paths
#        pdb_paths = set()
#        for b in benchmark_runs:
#            pdb_paths = pdb_paths.union(set([q.pdb_path for q in session.query(database.BenchmarkInputs).filter(database.BenchmarkInputs.benchmark_id == b.benchmark_id).all()]))
#
#        # Retrieve the number of jobs with structures
#        num_cases = len(pdb_paths)
#        benchmark_size = nstruct * num_cases
#        total_count = 0.0
#        pdb_counts = dict.fromkeys(pdb_paths, 0)
#        for r in session.execute('''
#                SELECT input_tag, COUNT(input_tag)
#                FROM structures
#                INNER JOIN batches ON structures.batch_id=batches.batch_id
#                INNER JOIN benchmark_protocols ON benchmark_protocols.protocol_id=batches.protocol_id
#                INNER JOIN benchmarks ON benchmarks.benchmark_id=benchmark_protocols.benchmark_id
#                WHERE benchmarks.name="{0}"
#                GROUP BY input_tag'''.format(benchmark_name)):
#            total_count += min(r[1], nstruct) # do not count extra jobs
#            assert(r[0] in pdb_paths)
#            pdb_counts[r[0]] = r[1]
#
#        num_failed = session.execute('''
#                SELECT COUNT(log_id) AS NumFailed
#                FROM tracer_logs
#                INNER JOIN benchmarks ON benchmarks.benchmark_id=tracer_logs.benchmark_id
#                WHERE stderr <> "" AND benchmarks.name="{0}"'''.format(benchmark_name))
#        for r in num_failed: num_failed = r[0]; break
#        progress = 100 * (total_count/benchmark_size)
#
#        return dict(
#            Messages = '\n'.join(messages),
#            Progress = progress,
#            StructureCount = num_cases,
#            nstruct = nstruct,
#            TotalCount = benchmark_size,
#            CompletedCount = int(total_count),
#            FailureCount = num_failed,
#            CountPerStructure = pdb_counts,
#        )


def get_progress_for_terminal(data_controller, database_name, benchmark_name, only_show_summary):
    '''Write progress to terminal.'''
    progress_data = get_progress(data_controller, database_name, benchmark_name)
    s = []
    if progress_data:
        progress, num_failed, nstruct = progress_data['Progress'], progress_data['FailureCount'], progress_data['nstruct']
        progress_fns = [colortext.mblue, colortext.mred, colortext.morange, colortext.myellow, colortext.mgreen]
        progress_fn = progress_fns[int(min(max(0, progress), 100)/25)]
        failed_cases_str = ''
        if num_failed:
            failed_cases_str = colortext.mred('\nFailed cases                : {0}'.format(num_failed))

        s = [progress_data['Messages'] or '']
        s.append('''Progress                                       : {0}
Number of cases                                : {1}{2}
Predictions per case                           : {3}
Total number of predictions                    : {4}
Completed predictions (extra jobs not counted) : {5}\n'''.format(progress_fn('%0.2f%%' % progress), progress_data['StructureCount'], failed_cases_str, nstruct, progress_data['TotalCount'], progress_data['CompletedCount']))

        if not only_show_summary:
            t = 'Completed jobs per case'
            s.append(t + '\n' + ('-' * len(t)))
            for k, v in sorted(progress_data['CountPerStructure'].iteritems()):
                progress_fn = progress_fns[int((float(min(max(0, v), nstruct))/float(nstruct))/0.25)]
                s.append('{0}: {1}'.format(k, progress_fn(v)))
            s.append('')
    return '\n'.join(s)


def report_progress(data_controller, database_name, benchmark_name, only_show_summary):
    print(get_progress_for_terminal(data_controller, database_name, benchmark_name, only_show_summary))


if __name__ == '__main__':
    try:
        from libraries import docopt
        arguments = docopt.docopt(__doc__)
        settings.load()
        benchmark_name = arguments['<benchmark_name>']
        summary = arguments['--summary']
        database_name = arguments['--database'] or settings.db_name
        data_controller = DataController(platform='database') if arguments['--database'] else DataController(platform='disk') 
        if arguments['--list']:
            name_list = data_controller.get_benchmark_list_by_name(database_name)
            if name_list:
                colortext.pgreen('\nList of available benchmarks in the {0} database:\n'.format(database_name))
                for n in name_list:
                    colortext.pcyan('  - {0}'.format(n))
                print('')
            else:
                colortext.pred('\nNo benchmarks defined in the {0} database.\n'.format(database_name))
        else:
            report_progress(data_controller, database_name, benchmark_name, summary)
    except KeyboardInterrupt:
        print


