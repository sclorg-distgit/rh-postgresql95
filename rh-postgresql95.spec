# Define SCL name
%{!?scl_name_prefix: %global scl_name_prefix sclo-}
%{!?scl_name_base: %global scl_name_base postgresql}
%{!?version_major: %global version_major 9}
%{!?version_minor: %global version_minor 5}
%{!?scl_name_version: %global scl_name_version %{version_major}%{version_minor}}
%{!?scl: %global scl %{scl_name_prefix}%{scl_name_base}%{scl_name_version}}

# Turn on new layout -- prefix for packages and location
# for config and variable files
# This must be before calling %%scl_package
%{!?nfsmountable: %global nfsmountable 1}

# Define SCL macros
%{?scl_package:%scl_package %{scl}}

# do not produce empty debuginfo package
%global debug_package %{nil}

Summary: Package that installs %{scl}
Name: %{scl}
Version: 2.0
Release: 10%{?dist}
License: GPLv2+
Group: Applications/File
Source0: README
Source1: LICENSE
Requires: scl-utils
Requires: %{scl_prefix}postgresql-server
BuildRequires: scl-utils-build help2man

%description
This is the main package for %{scl} Software Collection, which installs
necessary packages to use PostgreSQL %{version_major}.%{version_minor} server.
Software Collections allow to install more versions of the same
package by using alternative directory structure.
Install this package if you want to use PostgreSQL %{version_major}.%{version_minor}
server on your system.

%package runtime
Summary: Package that handles %{scl} Software Collection.
Group: Applications/File
Requires: scl-utils
Requires(post): policycoreutils-python libselinux-utils

%description runtime
Package shipping essential scripts to work with %{scl} Software Collection.

%package build
Summary: Package shipping basic build configuration
Group: Applications/File
Requires: scl-utils-build

%description build
Package shipping essential configuration macros to build %{scl} Software
Collection or packages depending on %{scl} Software Collection.

%package scldevel
Summary: Package shipping development files for %{scl}

%description scldevel
Package shipping development files, especially usefull for development of
packages depending on %{scl} Software Collection.

%prep
%setup -c -T

# This section generates README file from a template and creates man page
# from that file, expanding RPM macros in the template file.
cat <<'EOF' | tee README
%{expand:%(cat %{SOURCE0})}
EOF

# copy the license file so %%files section sees it
cp %{SOURCE1} .

%build
# generate a helper script that will be used by help2man
cat <<'EOF' | tee h2m_helper
#!/bin/bash
[ "$1" == "--version" ] && echo "%{?scl_name} %{version} Software Collection" || cat README
EOF
chmod a+x h2m_helper

# generate the man page
help2man -N --section 7 ./h2m_helper -o %{?scl_name}.7

%install
%{?scl_install}

# create and own dirs not covered by %%scl_install and %%scl_files
%if 0%{?rhel} >= 7 || 0%{?fedora} >= 15
mkdir -p %{buildroot}%{_mandir}/man{1,7,8}
%else
mkdir -p %{buildroot}%{_datadir}/aclocal
%endif

# create enable scriptlet that sets correct environment for collection
cat << EOF | tee -a %{buildroot}%{?_scl_scripts}/enable
# For binaries
export PATH="%{_bindir}\${PATH:+:\${PATH}}"
# For header files
export CPATH="%{_includedir}\${CPATH:+:\${CPATH}}"
# For libraries during build
export LIBRARY_PATH="%{_libdir}\${LIBRARY_PATH:+:\${LIBRARY_PATH}}"
# For libraries during linking
export LD_LIBRARY_PATH="%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}"
# For man pages; empty field makes man to consider also standard path
export MANPATH="%{_mandir}:\${MANPATH}"
# For Java Packages Tools to locate java.conf
export JAVACONFDIRS="%{_sysconfdir}/java:\${JAVACONFDIRS:-/etc/java}"
# For XMvn to locate its configuration file(s)
export XDG_CONFIG_DIRS="%{_sysconfdir}/xdg:\${XDG_CONFIG_DIRS:-/etc/xdg}"
# For systemtap
export XDG_DATA_DIRS="%{_datadir}\${XDG_DATA_DIRS:+:\${XDG_DATA_DIRS}}"
# For pkg-config
export PKG_CONFIG_PATH="%{_libdir}/pkgconfig\${PKG_CONFIG_PATH:+:\${PKG_CONFIG_PATH}}"
EOF

# generate rpm macros file for depended collections
cat << EOF | tee -a %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel
%%scl_%{scl_name_base} %{scl}
%%scl_prefix_%{scl_name_base} %{?scl_prefix}
EOF

# install generated man page
mkdir -p %{buildroot}%{_mandir}/man7/
install -m 644 %{?scl_name}.7 %{buildroot}%{_mandir}/man7/%{?scl_name}.7

%post runtime
# Simple copy of context from system root to SCL root.
# In case new version needs some additional rules or context definition,
# it needs to be solved in base system.
# semanage does not have -e option in RHEL-5, so we would
# have to have its own policy for collection.
semanage fcontext -a -e / %{?_scl_root} >/dev/null 2>&1 || :
semanage fcontext -a -e %{_root_sysconfdir} %{_sysconfdir} >/dev/null 2>&1 || :
semanage fcontext -a -e %{_root_localstatedir} %{_localstatedir} >/dev/null 2>&1 || :

selinuxenabled && load_policy || :
restorecon -R %{?_scl_root} >/dev/null 2>&1 || :
restorecon -R %{_sysconfdir} >/dev/null 2>&1 || :
restorecon -R %{_localstatedir} >/dev/null 2>&1 || :

%files

%if 0%{?rhel} >= 7 || 0%{?fedora} >= 15
%files runtime -f filesystem
%else
%files runtime
%{_datadir}/aclocal
%endif
%doc README LICENSE
%{?scl_files}
%{_mandir}/man7/%{?scl_name}.*

%files build
%doc LICENSE
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files scldevel
%doc LICENSE
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%changelog
* Mon Jan 18 2016 Pavel Kajaba <pkajaba@redhat.com> - 2.0-10
- Changed version 9.5

* Fri Mar 20 2015 Pavel Raiskup <praiskup@redhat.com> - 2.0-9
- move the postgresql-ctl context definition to main package

* Thu Mar 19 2015 Pavel Raiskup <praiskup@redhat.com> - 2.0-8
- fix SELinux context on starting binaries once more

* Wed Mar 18 2015 Pavel Raiskup <praiskup@redhat.com> - 2.0-7
- merge rhel6 & rhel7 rh-postgresql94 branches

* Wed Mar 18 2015 Pavel Raiskup <praiskup@redhat.com> - 2.0-6
- fix SELinux context on starting binaries
- rebuild for scl-utils change (#1200057)

* Wed Feb 18 2015 Honza Horak <hhorak@redhat.com> - 2.0-5
- Remove NFS register feature for questionable usage for DBs

* Thu Jan 29 2015 Jozef Mlich <jmlich@redhat.com> - 2.0-4
- %{_unitdir} is available only in RHEL7

* Mon Jan 26 2015 Honza Horak <hhorak@redhat.com> - 2.0-3
- Do not set selinux context  scl root during scl register

* Mon Jan 26 2015 Honza Horak <hhorak@redhat.com> - 2.0-2
- Use cat for README expansion, rather than include macro

* Sat Jan 17 2015 Honza Horak <hhorak@redhat.com>
- Apply many changes for new generation

* Mon Oct 13 2014 Honza Horak <hhorak@redhat.com> - 1.1-21
- Rebuild for s390x
  Resolves: #1152432

* Mon Mar 31 2014 Honza Horak <hhorak@redhat.com> - 1.1-20
- Fix path typo in README
  Related: #1061456

* Wed Feb 19 2014 Jozef Mlich <jmlich@redhat.com> - 1.1-19
- Release bump (and cherry pick from rhscl-1.1-postgresql92-rhel-7)
  Resloves: #1061456 

* Thu Feb 13 2014 Jozef Mlich <jmlich@redhat.com> - 1.1-18
- Resolves: #1058611 (postgresql92-build needs to depend
  on scl-utils-build)
- Add LICENSE, README and postgresql92.7 man page
  Resloves: #1061456 

* Wed Feb 12 2014 Honza Horak <hhorak@redhat.com> - 1.1-17
- Add -scldevel subpackage
  Resolves: #1063359

* Wed Dec 18 2013 Jozef Mlich <jmlich@redhat.com> 1-17
- release bump 
  Resolves #1038693

* Tue Nov 26 2013 Jozef Mlich <jmlich@redhat.com> 1-16
- By default, patch(1) creates backup files when chunks apply with offsets.
  Turn that off to ensure such files don't get included in RPMs.

* Fri Nov 22 2013 Honza Horak <hhorak@redhat.com> 1-15
- Rename variable to match postgresql package

* Mon Nov 18 2013 Jozef Mlich <jmlich@redhat.com> 1-14
- release bump

* Wed Oct  9 2013 Jozef Mlich <jmlich@redhat.com> 1-13
- release bump to scl 1.1

* Wed May 22 2013 Honza Horak <hhorak@redhat.com> 1-12
- Run semanage on whole root, BZ#956981 is fixed now
- Require semanage utility to be installed for -runtime package
- Fix MANPATH definition, colon in the end is correct (it means default)
  Resolves: BZ#966382

* Fri May  3 2013 Honza Horak <hhorak@redhat.com> 1-11
- Run semanage for all directories separately, since it has
  problems with definition for whole root

* Thu May  2 2013 Honza Horak <hhorak@redhat.com> 1-10
- Handle context of the init script
- Add better descriptions for packages

* Fri Apr 26 2013 Honza Horak <hhorak@redhat.com> 1-9
- fix escaping in PATH variable definition

* Mon Apr  8 2013 Honza Horak <hhorak@redhat.com> 1-8
- Don't require policycoreutils-python in RHEL-5 or older
- Require postgresql-server from the collection as main package
- Build separately on all arches
- Fix Environment variables definition

* Wed Feb 20 2013 Honza Horak <hhorak@redhat.com> 1-7
- Use %%setup macro to create safer build environment

* Fri Nov 09 2012 Honza Horak <hhorak@redhat.com> 1-6
- rename spec file to correspond with package name

* Thu Nov 08 2012 Honza Horak <hhorak@redhat.com> 1-5
- Mark service-environment as a config file

* Thu Oct 25 2012 Honza Horak <hhorak@redhat.com> 1-5
- create service-environment file to hold information about all collections,
  that should be enabled when service is starting
- added policycoreutils-python for semanage -e

* Thu Oct 18 2012 Honza Horak <hhorak@redhat.com> 1-3
- copy SELinux context from core mysql files

* Wed Oct 03 2012 Honza Horak <hhorak@redhat.com> 1-2
- update to postgresql-9.2 and rename to postgresql92

* Mon Mar 19 2012 Honza Horak <hhorak@redhat.com> 1-1
- initial packaging

