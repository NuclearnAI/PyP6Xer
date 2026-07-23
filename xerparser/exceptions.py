# PyP6XER
# Copyright (C) 2020, 2021 Hassan Emam <hassan@constology.com>
#
# This file is part of PyP6XER.
#
# PyP6XER library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License v2.1 as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyP6XER is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyP6XER.  If not, see <https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html>.


class XerParseError(ValueError):
    """A structural corruption detected while parsing an XER file.

    Subclasses ValueError so existing ValueError->4xx mappings keep working.
    ``kind`` is the stable cross-consumer contract:
    "malformed_row" | "ragged_row". Truncation is no longer a kind — it is
    surfaced as a ``Reader.truncated`` flag so consumers set their own policy.
    """

    def __init__(self, kind, detail, table=None, line=None):
        self.kind = kind
        self.table = table
        self.line = line
        self.detail = detail
        loc = f" in {table} at line {line}" if table else ""
        super().__init__(f"{kind}{loc}: {detail}")
