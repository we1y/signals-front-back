'use client'

import * as React from "react"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/common/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/common/tabs";
import { Button } from "@/components/ui/common/button";
import { ClipboardIcon } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { referralService } from "@/services/referral.service";
import { useTranslations } from "next-intl";
import ShareButton from "@/components/features/telegram/ShareButton";
import { toast } from "sonner";


export default function Referrals() {
  const { data } = useQuery({
    queryKey: ['referral'],
    queryFn: () => referralService.getUserReferrals()
  })

  const t = useTranslations("ReferralsDrawer");


  const copyToClipboard = async (text: any) => {
    try {
      await navigator.clipboard.writeText(text);
      toast(t("copied"));
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  return (
      <div className='space-y-4 w-full p-1.5 h-96 mb-4'>
        <Card className='text-center rounded-t-[42px]'>
            <CardHeader>
                <CardTitle>
                    {t("title")}
                </CardTitle>
            </CardHeader>
            <CardContent>
                0.00 USDT
            </CardContent>
        </Card>
        <Tabs defaultValue="system">
          <TabsList className="grid grid-cols-2">
            <TabsTrigger value="system">{t("systemtab")}</TabsTrigger>
            <TabsTrigger value="referrals">{t("referralstab")}</TabsTrigger>
          </TabsList>
          <TabsContent value="system">
            <Card className='text-center'>
              <CardHeader>
                <CardTitle>{t("share")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                  <Button className='w-full rounded-xl text-center m-2 hover:bg-primary-foreground' onClick={() => copyToClipboard(data ? data.referral_link : '')}>
                    {data ? data.referral_link : t('loading')} <ClipboardIcon />
                  </Button>
                  <ShareButton text={t("invite")}/>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="referrals">
            <Card className='text-center'>
              <CardHeader>
                <CardTitle>{t("referrals")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {data?.invited_users && data.invited_users.length > 0 ? (
                      data?.invited_users.map((referral) => (
                          <Card key={referral.id} className="border-2 border-foreground">
                              <CardHeader>{referral.telegram_id}</CardHeader>
                              <CardContent>
                                  {referral.referral_link}
                              </CardContent>
                              <CardFooter>
                                  {referral.invited_users.map((user) => (
                                    <p key={user.user_id} className="m-2">{user.telegram_id}</p>
                                  ))}
                              </CardFooter>
                          </Card>
                      ))
                  ) : (
                      <p>{t("noreferrals")}</p>
                  )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
  )
}