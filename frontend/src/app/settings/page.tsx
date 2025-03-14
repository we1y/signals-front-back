'use client'

import Plans from "@/components/features/drawers/Plans";
import BackButton from "@/components/features/telegram/BackButton";
import { Button } from "@/components/ui/common/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/common/card";
import { Drawer, DrawerTrigger, DrawerContent, DrawerTitle } from "@/components/ui/common/drawer";
import { useProfile } from "@/hooks/useProfile";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
import { useTranslations } from "next-intl";


export default function Settings() {
    const { user, isLoadingProfile } = useProfile();
    const t = useTranslations("Settings");

    return (
        <>
            <BackButton />
            <Card className='text-center m-2'>
                <CardHeader>
                    <CardTitle>
                        {t("title")}
                    </CardTitle>
                </CardHeader>
                <CardContent className='space-y-4'>
                    <Drawer>
                        <DrawerTrigger asChild>
                            <Button className='w-full h-full flex flex-col rounded-xl items-center text-xs p-2 hover:bg-primary-foreground'>
                                {t("work")}
                            </Button>
                        </DrawerTrigger>
                        <DrawerContent aria-describedby={undefined} className='flex items-center'>
                            <DrawerTitle>
                                <VisuallyHidden>{t("title")}</VisuallyHidden>
                            </DrawerTitle>
                            <Plans />
                        </DrawerContent>
                    </Drawer>
                    <div>
                        {t("language")}: Русский
                    </div>
                    <div>
                        {t("id")}: {isLoadingProfile ? t("loading") : user?.telegram_id}
                    </div>
                </CardContent>
            </Card>
        </>
    );
    }