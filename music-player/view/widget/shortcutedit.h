/**
 * Copyright (C) 2016 Deepin Technology Co., Ltd.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 **/

#pragma once

#include <QScopedPointer>
#include <QWidget>

class ShortcutEditPrivate;
class ShortcutEdit : public QWidget
{
    Q_OBJECT
public:
    explicit ShortcutEdit(QList<Qt::Key> keys, QWidget *parent = 0);
    ~ShortcutEdit();

signals:

public slots:

protected:
    virtual void paintEvent(QPaintEvent *e) Q_DECL_OVERRIDE;
    virtual void focusInEvent(QFocusEvent *e) Q_DECL_OVERRIDE;
    virtual void focusOutEvent(QFocusEvent *e) Q_DECL_OVERRIDE;
//    virtual void keyPressEvent(QKeyEvent *e) Q_DECL_OVERRIDE;

private:
    QScopedPointer<ShortcutEditPrivate> d_ptr;
    Q_DECLARE_PRIVATE_D(qGetPtrHelper(d_ptr), ShortcutEdit)
};
