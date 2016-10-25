/**
 * Copyright (C) 2016 Deepin Technology Co., Ltd.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 **/

#ifndef MUSICLISTMODEL_H
#define MUSICLISTMODEL_H

#include <QObject>
#include <QString>
#include <QStringList>
#include <QMap>
#include <QTime>

class MusicInfo
{
public:
    QString id;
    QString url;
    QString title;
    QString artist;
    QString album;
    QString filetype;
    qint64  length;
    qint64  track;
    qint64  size;
    bool    favourite;
};

typedef QList<MusicInfo>    MusicList;

class MusicListInfo
{
public:
    QString id;
    QString displayName;
    QString url;
    QString icon;

    bool    editmode;
    bool    readonly;

    QStringList                 musicIds;
    QMap<QString, MusicInfo>    musicMap;
};

inline QString lengthString(qint64 length)
{
    QTime t(static_cast<int>(length / 3600), length % 3600 / 60, length % 60);
    return t.toString("mm:ss");
}

inline QString sizeString(qint64 sizeByte)
{
    QString text;
    if (sizeByte < 1024) {
        text.sprintf("%.1fB", sizeByte / 1.0);
        return text;
    }
    if (sizeByte < 1024 * 1024) {
        text.sprintf("%.1fK", sizeByte / 1024.0);
        return text;
    }
    if (sizeByte < 1024 * 1024 * 1024) {
        text.sprintf("%.1fM", sizeByte / 1024.0 / 1024.0);
        return text;
    }
    text.sprintf("%.1fG", sizeByte / 1024.0 / 1024.0 / 1024.0);
    return text;
}

Q_DECLARE_METATYPE(MusicInfo);
Q_DECLARE_METATYPE(MusicListInfo);

#endif // MUSICLISTMODEL_H
