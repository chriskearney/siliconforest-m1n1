/* SPDX-License-Identifier: GPL-2.0-or-later */

#ifndef MITIGATIONS_H
#define MITIGATIONS_H

void mitigations_configure(const char *config);
int mitigations_perform(void);

#endif
