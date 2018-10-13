======================
Development Guidelines
======================
We don't have any strict development guidlines, basically you can contribute
in whatever way you are capable of, and as long as your code does not break
too many things and adds value it will be accepted. But here are a few
recommendations that should make it easier if this is your first time
contributing to a project like this.

In general we use a development workflow similar to `GitHub Flow
<https://guides.github.com/introduction/flow>`_. If you are not
familiar with that don't worry, it is very straightforward.

Creating a Local Checkout
=========================
If you want to make changes to QtPyVCP the first step is to create your own fork
of the repository. This allows you to create feature branches and push changes
to your personal fork so that others can view and test them, without you having
to worry about messing anything up in the main repository. It is easy to fork,
but here is a `quick tutorial <https://help.github.com/articles/fork-a-repo>`_.

Once your fork is created you can clone it to your local machine.

.. code:: sh

   $ git clone https://github.com/YOUR-USERNAME/REPOSITORY.git

Now that you have a copy of the repository, create a branch for the feature or
bug you would like to work on.

.. code:: sh

   $ git checkout -b my-feature

   $ git status
   On branch my-feature
   nothing to commit, working tree clean

.. admonition:: ProTip

    Shhhh, don't tell, but we like to use a GUI git client called `GitKraken
    <https://www.gitkraken.com/>`_. It makes even complicated git tasks as
    simple as a few clicks, and the visual commit history alone is worth
    every penny! Best part, it's free (for non commercial use).

Commit Guidelines
=================
Now you are ready to start working! Make changes to files and commit them to
your new branch. I like to preface my commit messages with a descriptor code.
This makes it easier for someone reviewing the commit history to see what type
of changes were made in each commit.

====  ===
Code  Description
====  ===
API   an (incompatible) API change
BLD   change related to building
BUG   bug fix
DEP   deprecate something, or remove a deprecated object
DEV   development tool or utility
DOC   documentation
ENH   enhancement
MNT   maintenance commit (refactoring, typos, etc.)
REV   revert an earlier commit
STY   style fix (whitespace, PEP8)
TST   addition or modification of tests
REL   related to a release (increment version numbers etc.)
WIP   work in progress
SIM   change related to linuxcnc sim configs
VCP   work on example VCPs
====  ===

It is also recommended to write docstrings for all python classes and functions.
These are automatically converted by Sphinx into HTML documentation. Docstrings
should follow the Google style guidelines, a complete example of which is `here
<https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`__.

Merging Changes
===============
Once you are happy with your code, ``push`` it back to your fork on GitHub.

.. code:: sh

   $ git push origin my-feature

You should now be able to create a Pull Request back to the original repository.
Once the changes are checked and reviewed the Pull Request can be merged.

Syncing your Local Checkout
===========================
Inevitably, changes to the upstream repository will occur and you will need to
update your local checkout to reflect those. The first step is to make your
local checkout aware of the upstream repository. If this is done correctly, you
should see something like this:

.. code:: sh

   $ git remote add upstream https://github.com/UPSTREAM-ORG/REPOSITORY.git
   $ git remote -v
   origin   https://github.com/YOUR-USERNAME/REPOSITORY.git (fetch)
   origin   https://github.com/YOUR-USERNAME/REPOSITORY.git (push)
   upstream https://github.com/UPSTREAM-ORG/REPOSITORY.git (fetch)
   upstream https://github.com/UPSTREAM-ORG/REPOSITORY.git (push)

Now, you need to fetch any changes from the upstream repository. ``git fetch``
will grab the latest commits that were merged since we made our own fork

.. code:: sh

   $ git fetch upstream


Ideally you haven't made any changes to your ``master`` branch. So you should be
able to merge the latest ``master`` branch from the upstream repository without
concern. All you need to do is to switch to your ``master`` branch, and pull in
the changes from the upstream remote. It is usually a good idea to push any
changes back to your fork as well.

.. code:: sh

   $ git checkout master
   $ git pull upstream master
   $ git push origin master

Finally, you need to update your feature-branch to have the new changes. It is
best to use a ``git rebase`` to take the local changes, remove them temporarily,
pull the upstream changes, and then re-add the local changes on the
tip of the commit history. This avoids extraneous merge commits that clog the
commit history of the branch. A more in-depth discussion can be found `here
<https://www.atlassian.com/git/tutorials/merging-vs-rebasing>`__. This process
would bee something look like this:

.. code:: sh

   $ git checkout my-feature
   $ git rebase upstream/master

.. note::
   A rebase should not be done if you think that anyone else is also
   working on the branch. Rebasing re-writes the commit history so
   any other checkout of the same branch will have the old history
   so when they are eventually merged there will be duplicates of all
   the rebased commits. Kinda defeats the purpose of the rebase :)
